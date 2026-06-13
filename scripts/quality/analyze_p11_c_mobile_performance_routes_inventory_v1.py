from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_REL = "app/api/mobile/performance_routes.py"


DOMAIN_HINTS = {
    "dashboard": ["dashboard", "summary", "overview", "stats", "chart"],
    "tasks": ["task", "tasks", "gorev", "assignment", "degerlendirme", "evaluation"],
    "score": ["score", "puan", "rating", "criteria", "kriter", "form"],
    "period": ["period", "donem", "calendar", "active", "start", "end"],
    "report": ["report", "rapor", "export", "card", "karne"],
    "hierarchy": ["hierarchy", "amir", "manager", "chain", "unit"],
    "approval": ["approval", "onay", "president", "baskan", "publish"],
    "utility": ["health", "ping", "version", "status", "config"],
}

HIGH_RISK_HINTS = (
    "commit(", "rollback(", "db.session.add", "db.session.delete", ".delete(",
    "request.json", "request.form", "request.get_json", "current_user",
    "publish", "approve", "approval", "onay", "score", "puan",
)

DB_READ_HINTS = (
    "db.session", ".query", ".filter", ".filter_by", ".join", ".all(", ".first(", ".get(",
)


def node_lines(node: ast.AST) -> tuple[int, int, int]:
    start = getattr(node, "lineno", 0) or 0
    end = getattr(node, "end_lineno", start) or start
    return start, end, max(0, end - start + 1)


def segment(lines: list[str], start: int, end: int) -> str:
    if start <= 0 or end <= 0:
        return ""
    return "\n".join(lines[start - 1:end])


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts = []
        cur: ast.AST | None = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return ""


def decorator_name(dec: ast.AST) -> str:
    func = dec.func if isinstance(dec, ast.Call) else dec
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def literal_string(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def extract_methods_from_keywords(dec: ast.Call) -> list[str]:
    for kw in dec.keywords:
        if kw.arg != "methods":
            continue
        value = kw.value
        if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
            methods = []
            for elt in value.elts:
                val = literal_string(elt)
                if val:
                    methods.append(val.upper())
            return methods
    return []


def decorators_text(node: ast.AST) -> list[str]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    out = []
    for dec in node.decorator_list:
        try:
            out.append(ast.unparse(dec))
        except Exception:
            out.append("")
    return out


def extract_routes(node: ast.AST) -> list[dict[str, Any]]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    rows: list[dict[str, Any]] = []
    for dec in node.decorator_list:
        name = decorator_name(dec)
        if name not in {"route", "get", "post", "put", "patch", "delete"}:
            continue
        if not isinstance(dec, ast.Call):
            continue
        route = literal_string(dec.args[0]) if dec.args else ""
        if not route:
            try:
                route = ast.unparse(dec)
            except Exception:
                route = f"<{name}>"
        methods = extract_methods_from_keywords(dec)
        if name in {"get", "post", "put", "patch", "delete"} and not methods:
            methods = [name.upper()]
        if name == "route" and not methods:
            methods = ["GET"]
        rows.append({
            "route": route,
            "methods": sorted(set(methods)),
            "decorator_name": name,
        })
    return rows


def classify(name: str, routes: list[dict[str, Any]], src: str) -> str:
    route_text = " ".join(r["route"] for r in routes)
    low = f"{name}\n{route_text}\n{src}".lower()
    scores = Counter()
    for domain, hints in DOMAIN_HINTS.items():
        for hint in hints:
            if hint.lower() in low:
                scores[domain] += 1
    if not scores:
        return "general"
    return scores.most_common(1)[0][0]


def analyze_function(node: ast.AST, lines: list[str]) -> dict[str, Any]:
    start, end, count = node_lines(node)
    src = segment(lines, start, end)
    name = getattr(node, "name", "")
    routes = extract_routes(node)
    decorators = decorators_text(node)
    domain = classify(name, routes, src)

    calls = []
    names = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            cn = call_name(sub.func)
            if cn:
                calls.append(cn)
        elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            names.append(sub.id)

    high_risk = sorted(h for h in HIGH_RISK_HINTS if h.lower() in src.lower())
    db_read = sorted(h for h in DB_READ_HINTS if h.lower() in src.lower())
    methods = sorted({m for r in routes for m in r["methods"]})
    has_write_method = any(m in {"POST", "PUT", "PATCH", "DELETE"} for m in methods)
    has_route = bool(routes)

    if not has_route:
        decision = "NOT_ROUTE_HELPER"
        risk_level = "LOW"
        reason = "Route decorator yok."
    elif high_risk or has_write_method:
        decision = "DEFER_HIGH_RISK_WRITE_OR_SCORE"
        risk_level = "HIGH"
        reason = "Puan/onay/yayın/write veya POST/PUT/PATCH/DELETE riski var."
    elif count >= 90:
        decision = "DEFER_LARGE_ROUTE"
        risk_level = "HIGH"
        reason = "Büyük route; özel refactor planı gerekir."
    elif db_read and count > 55:
        decision = "REVIEW_DB_READ_ROUTE"
        risk_level = "MEDIUM"
        reason = "DB okuma içeriyor ve orta/büyük boy."
    elif domain in {"utility", "dashboard", "report"} and count <= 55:
        decision = "FIRST_SPLIT_CANDIDATE"
        risk_level = "LOW_MEDIUM"
        reason = "Küçük GET/read endpoint; ilk bridge split adayı olabilir."
    elif count <= 45:
        decision = "LOW_RISK_ROUTE_CANDIDATE"
        risk_level = "MEDIUM"
        reason = "Küçük GET route; domain/smoke kontrolü ile aday olabilir."
    else:
        decision = "REVIEW_ROUTE"
        risk_level = "MEDIUM"
        reason = "Elle değerlendirme gerekir."

    return {
        "name": name,
        "start": start,
        "end": end,
        "lines": count,
        "decorators": decorators,
        "routes": routes,
        "methods": methods,
        "domain": domain,
        "call_sample": sorted(set(calls))[:80],
        "names_sample": sorted(set(names))[:80],
        "high_risk_hits": high_risk,
        "db_read_hits": db_read,
        "decision": decision,
        "risk_level": risk_level,
        "reason": reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_QUALITY_10_10_P11_C_MOBILE_PERFORMANCE_ROUTES_INVENTORY_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = target.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    tree = ast.parse(text)

    imports = []
    assignments = []
    functions = []
    classes = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start, end, count = node_lines(node)
            imports.append({"start": start, "end": end, "source": segment(lines, start, end)})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            start, end, count = node_lines(node)
            assignments.append({"start": start, "end": end, "lines": count, "source": segment(lines, start, end)[:220]})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(analyze_function(node, lines))
        elif isinstance(node, ast.ClassDef):
            start, end, count = node_lines(node)
            classes.append({"name": node.name, "start": start, "end": end, "lines": count})

    route_functions = [f for f in functions if f["routes"]]
    large_functions = [f for f in functions if f["lines"] >= 80]
    first_candidates = [f for f in route_functions if f["decision"] == "FIRST_SPLIT_CANDIDATE"]
    low_candidates = [f for f in route_functions if f["decision"] == "LOW_RISK_ROUTE_CANDIDATE"]
    review_candidates = [f for f in route_functions if f["decision"] in {"REVIEW_DB_READ_ROUTE", "REVIEW_ROUTE"}]
    deferred = [f for f in route_functions if f["decision"].startswith("DEFER")]

    by_decision = Counter(f["decision"] for f in functions)
    by_domain = Counter(f["domain"] for f in route_functions)
    by_risk = Counter(f["risk_level"] for f in route_functions)
    by_decorator = Counter(r["decorator_name"] for f in route_functions for r in f["routes"])

    report = {
        "target_file": TARGET_REL,
        "line_count": len(lines),
        "import_count": len(imports),
        "assignment_count": len(assignments),
        "class_count": len(classes),
        "function_count": len(functions),
        "route_function_count": len(route_functions),
        "large_function_count": len(large_functions),
        "decorator_summary": dict(by_decorator.most_common()),
        "decision_summary": dict(by_decision.most_common()),
        "route_domain_summary": dict(by_domain.most_common()),
        "route_risk_summary": dict(by_risk.most_common()),
        "large_functions": large_functions,
        "first_split_candidates": first_candidates,
        "low_risk_candidates": low_candidates,
        "review_candidates": review_candidates,
        "deferred_candidates": deferred,
        "all_functions": functions,
        "safety_strategy": [
            "Performans puanlama, onay, yayın, değerlendirme kaydetme veya POST endpointleri ilk split kapsamına alınmamalı.",
            "İlk gerçek split yalnızca küçük GET/read veya utility endpointlerle yapılmalı.",
            "URL path, JSON cevap formatı ve mobil Flutter beklentileri korunmalı.",
            "Her taşıma sonrası compileall, audit ve mobil API smoke test yapılmalı.",
        ],
        "next_step": "P11-C1: güvenli düşük riskli GET/read endpoint varsa bridge split adayı seçme.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_c_mobile_performance_routes_inventory_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_c_mobile_performance_routes_inventory_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-C Mobile Performance Routes Envanteri")
    md.append("")
    md.append(f"- Dosya: `{TARGET_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Fonksiyon sayısı: {len(functions)}")
    md.append(f"- Route fonksiyon sayısı: {len(route_functions)}")
    md.append(f"- Büyük fonksiyon sayısı: {len(large_functions)}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for k, v in by_decision.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Route Domain Özeti")
    md.append("")
    for k, v in by_domain.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## İlk Split Adayları")
    md.append("")
    if first_candidates:
        for f in first_candidates:
            route = ", ".join(r["route"] for r in f["routes"])
            md.append(f"- `{f['name']}` ({f['domain']}) satır {f['start']}-{f['end']} ({f['lines']}), route={route}")
    else:
        md.append("- İlk split adayı bulunmadı.")
    md.append("")
    md.append("## Ertelenen Yüksek Riskliler")
    md.append("")
    for f in deferred[:100]:
        route = ", ".join(r["route"] for r in f["routes"])
        md.append(f"- `{f['name']}` ({f['domain']}) satır {f['start']}-{f['end']} ({f['lines']}), route={route}, risk={', '.join(f['high_risk_hits']) or '-'}")
    md.append("")
    md.append("## Güvenlik Stratejisi")
    md.append("")
    for item in report["safety_strategy"]:
        md.append(f"- {item}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={len(lines)}")
    print(f"import_count={len(imports)}")
    print(f"assignment_count={len(assignments)}")
    print(f"class_count={len(classes)}")
    print(f"function_count={len(functions)}")
    print(f"route_function_count={len(route_functions)}")
    print(f"large_function_count={len(large_functions)}")
    print("BYS360_QUALITY_10_10_P11_C_DECORATOR_SUMMARY")
    for k, v in by_decorator.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_C_DECISION_SUMMARY")
    for k, v in by_decision.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_C_ROUTE_RISK_SUMMARY")
    for k, v in by_risk.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_C_FIRST_SPLIT_CANDIDATES")
    for f in first_candidates[:args.limit]:
        route = ",".join(r["route"] for r in f["routes"])
        methods = ",".join(f["methods"]) if f["methods"] else "-"
        print(f"{f['lines']:>4} | {f['domain']} | {f['start']}-{f['end']} | {f['name']} | methods={methods} | route={route}")
    print("BYS360_QUALITY_10_10_P11_C_LOW_RISK_CANDIDATES")
    for f in low_candidates[:args.limit]:
        route = ",".join(r["route"] for r in f["routes"])
        methods = ",".join(f["methods"]) if f["methods"] else "-"
        print(f"{f['lines']:>4} | {f['domain']} | {f['start']}-{f['end']} | {f['name']} | methods={methods} | route={route}")
    print("BYS360_QUALITY_10_10_P11_C_LARGE_FUNCTIONS")
    for f in large_functions[:args.limit]:
        route = ",".join(r["route"] for r in f["routes"]) if f["routes"] else "-"
        print(f"{f['lines']:>4} | {f['domain']} | {f['start']}-{f['end']} | {f['name']} | route={route} | decision={f['decision']}")
    print(f"mobile_performance_routes_inventory_json={json_out}")
    print(f"mobile_performance_routes_inventory_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_C_MOBILE_PERFORMANCE_ROUTES_INVENTORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
