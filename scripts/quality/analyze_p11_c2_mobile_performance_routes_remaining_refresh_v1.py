from __future__ import annotations

import argparse
import ast
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TARGET_REL = "app/api/mobile/performance_routes.py"

DOMAIN_HINTS = {
    "dashboard": ["dashboard", "summary", "overview", "stats", "chart"],
    "tasks": ["task", "tasks", "gorev", "assignment", "degerlendirme", "evaluation"],
    "score": ["score", "puan", "rating", "criteria", "kriter", "form"],
    "period": ["period", "donem", "calendar", "active", "start", "end", "category", "reminder", "weight"],
    "report": ["report", "rapor", "export", "card", "karne", "manager-view"],
    "hierarchy": ["hierarchy", "amir", "manager", "chain", "unit"],
    "approval": ["approval", "onay", "president", "baskan", "publish"],
    "utility": ["health", "ping", "version", "status", "config"],
}

HIGH_RISK_HINTS = (
    "commit(", "rollback(", "db.session.add", "db.session.delete", ".delete(",
    "request.json", "request.form", "request.get_json", "current_user",
    "publish", "approve", "approval", "onay", "score", "puan", "submit",
    "assignment_id", "score-form",
)

DB_READ_HINTS = (
    "db.session", ".query", ".filter", ".filter_by", ".join", ".all(", ".first(", ".get(",
)

MOVED_BRIDGE_MARKERS = (
    "P11-C1",
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
    domain = classify(name, routes, src)

    calls = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            cn = call_name(sub.func)
            if cn:
                calls.append(cn)

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
    elif count <= 35:
        decision = "LOW_RISK_ROUTE_CANDIDATE"
        risk_level = "MEDIUM"
        reason = "Küçük GET route; domain/smoke kontrolü ile aday olabilir."
    elif count <= 55:
        decision = "REVIEW_LIGHT_ROUTE"
        risk_level = "MEDIUM"
        reason = "Görece küçük GET route; taşıma öncesi elle kontrol gerekir."
    else:
        decision = "REVIEW_ROUTE"
        risk_level = "MEDIUM"
        reason = "Elle değerlendirme gerekir."

    return {
        "name": name,
        "start": start,
        "end": end,
        "lines": count,
        "routes": routes,
        "methods": methods,
        "domain": domain,
        "call_sample": sorted(set(calls))[:80],
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

    print("BYS360_QUALITY_10_10_P11_C2_MOBILE_PERFORMANCE_ROUTES_REMAINING_REFRESH_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = target.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    tree = ast.parse(text)

    functions = [analyze_function(n, lines) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    route_functions = [f for f in functions if f["routes"]]

    by_decision = Counter(f["decision"] for f in functions)
    by_domain = Counter(f["domain"] for f in route_functions)
    by_risk = Counter(f["risk_level"] for f in route_functions)
    by_decorator = Counter(r["decorator_name"] for f in route_functions for r in f["routes"])

    low_candidates = [f for f in route_functions if f["decision"] == "LOW_RISK_ROUTE_CANDIDATE"]
    light_review = [f for f in route_functions if f["decision"] == "REVIEW_LIGHT_ROUTE"]
    review_db = [f for f in route_functions if f["decision"] == "REVIEW_DB_READ_ROUTE"]
    deferred = [f for f in route_functions if f["decision"].startswith("DEFER")]

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for f in low_candidates + light_review:
        grouped[f["domain"]].append(f)

    recommendation = {
        "recommended_domain": None,
        "recommended_functions": [],
        "reason": "C1 sonrası kalan route’lar büyük ölçüde puan/onay/write/score veya daha hassas performans işlem tarafına kaymıştır. Bu dosyada gerçek split’i zorlamadan durmak daha güvenlidir.",
        "next_step": "P11-C burada durdurulmalı; P1 için teknik UI terim temizliği veya assistant JS envanterine geçilmeli.",
    }

    # Only recommend if there are non-score, non-approval, non-write small GET candidates.
    safe_priority = ["utility", "dashboard", "report", "period", "tasks"]
    for domain in safe_priority:
        funcs = grouped.get(domain, [])
        safe_funcs = [
            f for f in funcs
            if not f["high_risk_hits"] and "POST" not in f["methods"] and f["lines"] <= 35
        ]
        if safe_funcs:
            recommendation = {
                "recommended_domain": domain,
                "recommended_functions": safe_funcs,
                "reason": "Kalan küçük GET endpointleri içinde düşük riskli görünen grup var; yine de önce elle kontrol edilmelidir.",
                "next_step": "P11-C3 seçilen düşük riskli GET grubunu bridge ile ayırma.",
            }
            break

    report = {
        "target_file": TARGET_REL,
        "line_count": len(lines),
        "function_count": len(functions),
        "route_function_count": len(route_functions),
        "decorator_summary": dict(by_decorator.most_common()),
        "decision_summary": dict(by_decision.most_common()),
        "route_domain_summary": dict(by_domain.most_common()),
        "route_risk_summary": dict(by_risk.most_common()),
        "low_risk_candidates": low_candidates,
        "light_review_candidates": light_review,
        "review_db_candidates": review_db,
        "deferred_candidates": deferred,
        "grouped_candidates": {k: v for k, v in grouped.items()},
        "recommendation": recommendation,
        "moved_bridge_markers_found": [m for m in MOVED_BRIDGE_MARKERS if m in text],
        "safety_strategy": [
            "Puanlama, onay, yayın, score submit, POST ve commit/rollback içeren endpointlere dokunulmayacak.",
            "Kalan route’larda güvenli küçük GET adayı yoksa bu dosyada durulacak.",
            "P1 azaltma için bundan sonra teknik UI terim temizliği veya assistant JS envanteri daha doğru olabilir.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_c2_mobile_performance_routes_remaining_refresh_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_c2_mobile_performance_routes_remaining_refresh_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-C2 Mobile Performance Routes Remaining Refresh")
    md.append("")
    md.append(f"- Dosya: `{TARGET_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Fonksiyon sayısı: {len(functions)}")
    md.append(f"- Kalan route fonksiyon sayısı: {len(route_functions)}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for k, v in by_decision.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Öneri")
    md.append("")
    md.append(f"- Domain: `{recommendation['recommended_domain'] or '-'}`")
    md.append(f"- Gerekçe: {recommendation['reason']}")
    if recommendation["recommended_functions"]:
        for f in recommendation["recommended_functions"]:
            route = ", ".join(r["route"] for r in f["routes"])
            md.append(f"- `{f['name']}` satır {f['start']}-{f['end']} ({f['lines']}), route={route}, decision={f['decision']}")
    md.append("")
    md.append("## Düşük Risk / Hafif İnceleme Adayları")
    md.append("")
    for f in (low_candidates + light_review)[:100]:
        route = ", ".join(r["route"] for r in f["routes"])
        md.append(f"- `{f['name']}` ({f['domain']}) satır {f['start']}-{f['end']} ({f['lines']}), route={route}, decision={f['decision']}, risk={', '.join(f['high_risk_hits']) or '-'}")
    md.append("")
    md.append("## Ertelenen Yüksek Riskliler")
    md.append("")
    for f in deferred[:100]:
        route = ", ".join(r["route"] for r in f["routes"])
        md.append(f"- `{f['name']}` ({f['domain']}) satır {f['start']}-{f['end']} ({f['lines']}), route={route}, risk={', '.join(f['high_risk_hits']) or '-'}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={len(lines)}")
    print(f"function_count={len(functions)}")
    print(f"route_function_count={len(route_functions)}")
    print("BYS360_QUALITY_10_10_P11_C2_DECORATOR_SUMMARY")
    for k, v in by_decorator.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_C2_DECISION_SUMMARY")
    for k, v in by_decision.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_C2_ROUTE_RISK_SUMMARY")
    for k, v in by_risk.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_C2_LOW_OR_LIGHT_CANDIDATES")
    for f in (low_candidates + light_review)[:args.limit]:
        route = ",".join(r["route"] for r in f["routes"])
        methods = ",".join(f["methods"]) if f["methods"] else "-"
        risk = ",".join(f["high_risk_hits"]) if f["high_risk_hits"] else "-"
        print(f"{f['lines']:>4} | {f['domain']} | {f['decision']} | {f['start']}-{f['end']} | {f['name']} | methods={methods} | route={route} | risk={risk}")
    print("BYS360_QUALITY_10_10_P11_C2_RECOMMENDATION")
    print(f"recommended_domain={recommendation['recommended_domain'] or '-'}")
    if recommendation["recommended_functions"]:
        print("recommended_functions=" + ",".join(f["name"] for f in recommendation["recommended_functions"]))
    else:
        print("recommended_functions=-")
    print(f"remaining_refresh_json={json_out}")
    print(f"remaining_refresh_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_C2_MOBILE_PERFORMANCE_ROUTES_REMAINING_REFRESH_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
