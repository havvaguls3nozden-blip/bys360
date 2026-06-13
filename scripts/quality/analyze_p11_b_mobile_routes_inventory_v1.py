from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_REL = "app/api/mobile/routes.py"


DOMAIN_HINTS = {
    "auth": ["login", "logout", "token", "auth", "session", "password", "captcha"],
    "dashboard": ["dashboard", "home", "summary", "widget", "stats"],
    "personnel": ["personnel", "personel", "employee", "profile", "hr", "attendance"],
    "support": ["support", "ticket", "destek", "talep"],
    "survey": ["survey", "anket", "question", "answer"],
    "communication": ["message", "communication", "duyuru", "announcement", "notification"],
    "assistant": ["assistant", "asistan", "ai_agent", "chat"],
    "settings": ["settings", "ayar", "role", "permission", "menu"],
    "utility": ["health", "ping", "version", "config", "status"],
}

RISK_HINTS = (
    "db.session", ".query", ".filter", ".filter_by", ".join", ".all(", ".first(",
    ".get(", "request.", "current_user", "session[", "commit(", "rollback(",
    "jwt", "token", "password", "set_password", "check_password_hash",
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


def decorators_text(node: ast.AST) -> list[str]:
    out = []
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return out
    for dec in node.decorator_list:
        try:
            out.append(ast.unparse(dec))
        except Exception:
            out.append("")
    return out


def extract_routes_from_decorators(decorators: list[str]) -> list[str]:
    routes = []
    for dec in decorators:
        if ".route(" in dec or dec.startswith("route(") or ".get(" in dec or ".post(" in dec:
            # Pull first quoted value where possible
            m = re.search(r"['\"]([^'\"]+)['\"]", dec)
            if m:
                routes.append(m.group(1))
            else:
                routes.append(dec)
    return routes


def classify(name: str, route: str, src: str) -> str:
    low = f"{name}\n{route}\n{src}".lower()
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
    decorators = decorators_text(node)
    routes = extract_routes_from_decorators(decorators)
    calls = []
    names = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            cname = call_name(sub.func)
            if cname:
                calls.append(cname)
        elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
            names.append(sub.id)

    risk_hits = sorted(h for h in RISK_HINTS if h.lower() in src.lower())
    route_text = " ".join(routes)
    domain = classify(name, route_text, src)

    if routes and count >= 90:
        decision = "SPLIT_ROUTE_CANDIDATE_HIGH"
        reason = "Route fonksiyonu büyük; domain modüle ayrılmadan önce özel smoke test gerekir."
    elif routes:
        decision = "ROUTE_GROUP_CANDIDATE"
        reason = "Route endpointi; aynı URL korunarak domain dosyasına taşınabilir aday."
    elif count >= 80:
        decision = "HELPER_SPLIT_REVIEW"
        reason = "Büyük yardımcı fonksiyon; bağımlılık kontrolü gerekir."
    else:
        decision = "KEEP_OR_LOW_PRIORITY"
        reason = "Küçük yardımcı veya düşük öncelikli blok."

    return {
        "name": name,
        "start": start,
        "end": end,
        "lines": count,
        "decorators": decorators,
        "routes": routes,
        "domain": domain,
        "risk_hits": risk_hits,
        "call_sample": sorted(set(calls))[:80],
        "names_sample": sorted(set(names))[:80],
        "decision": decision,
        "reason": reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_QUALITY_10_10_P11_B_MOBILE_ROUTES_INVENTORY_START")
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
    high_candidates = [f for f in functions if f["decision"] == "SPLIT_ROUTE_CANDIDATE_HIGH"]
    route_candidates = [f for f in functions if f["decision"] == "ROUTE_GROUP_CANDIDATE"]

    by_domain = Counter(f["domain"] for f in functions)
    route_by_domain = Counter(f["domain"] for f in route_functions)
    by_decision = Counter(f["decision"] for f in functions)

    proposed_modules = {
        "app/api/mobile/auth_routes.py": ["auth"],
        "app/api/mobile/dashboard_routes.py": ["dashboard"],
        "app/api/mobile/personnel_routes.py": ["personnel"],
        "app/api/mobile/support_survey_routes.py": ["support", "survey"],
        "app/api/mobile/communication_routes.py": ["communication"],
        "app/api/mobile/assistant_routes.py": ["assistant"],
        "app/api/mobile/settings_routes.py": ["settings"],
        "app/api/mobile/utility_routes.py": ["utility"],
    }

    report = {
        "target_file": TARGET_REL,
        "line_count": len(lines),
        "import_count": len(imports),
        "assignment_count": len(assignments),
        "class_count": len(classes),
        "function_count": len(functions),
        "route_function_count": len(route_functions),
        "large_function_count": len(large_functions),
        "high_split_candidate_count": len(high_candidates),
        "function_domain_summary": dict(by_domain.most_common()),
        "route_domain_summary": dict(route_by_domain.most_common()),
        "decision_summary": dict(by_decision.most_common()),
        "large_functions": large_functions,
        "high_split_candidates": high_candidates,
        "route_candidates": route_candidates,
        "all_functions": functions,
        "proposed_modules": proposed_modules,
        "safety_strategy": [
            "Bu aşamada kod taşınmayacak; mobil route/domain haritası çıkarılacak.",
            "URL path değerleri ve endpoint davranışları korunmadan gerçek split yapılmayacak.",
            "İlk gerçek refactor sadece düşük riskli utility/health veya küçük route grubuyla yapılmalı.",
            "Auth/token/login route'ları en sona bırakılmalı.",
            "Her taşıma sonrası compileall, mobil API smoke ve Flutter smoke test çalıştırılmalı.",
        ],
        "next_step": "P11-B1: En küçük ve düşük riskli route grubunu bridge ile ayırma adayı belirleme.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_b_mobile_routes_inventory_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_b_mobile_routes_inventory_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-B Mobile Routes Envanteri")
    md.append("")
    md.append(f"- Dosya: `{TARGET_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Fonksiyon sayısı: {len(functions)}")
    md.append(f"- Route fonksiyon sayısı: {len(route_functions)}")
    md.append(f"- Büyük fonksiyon sayısı: {len(large_functions)}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for key, count in by_decision.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Route Domain Dağılımı")
    md.append("")
    for key, count in route_by_domain.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Büyük Fonksiyonlar")
    md.append("")
    if large_functions:
        for f in large_functions:
            route = ", ".join(f["routes"]) if f["routes"] else "-"
            md.append(f"- `{f['name']}` satır {f['start']}-{f['end']} ({f['lines']} satır), domain={f['domain']}, route={route}")
    else:
        md.append("- 80 satır üstü fonksiyon bulunmadı.")
    md.append("")
    md.append("## Önerilen Modül Ayrımı")
    md.append("")
    for file, domains in proposed_modules.items():
        md.append(f"- `{file}`: {', '.join(domains)}")
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
    print(f"high_split_candidate_count={len(high_candidates)}")
    print("BYS360_QUALITY_10_10_P11_B_DECISION_SUMMARY")
    for key, count in by_decision.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P11_B_ROUTE_DOMAIN_SUMMARY")
    for key, count in route_by_domain.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P11_B_LARGE_FUNCTIONS")
    for f in large_functions[:args.limit]:
        route = ",".join(f["routes"]) if f["routes"] else "-"
        risk = ",".join(f["risk_hits"]) if f["risk_hits"] else "-"
        print(f"{f['lines']:>4} | {f['domain']} | {f['start']}-{f['end']} | {f['name']} | route={route} | risk={risk}")
    print(f"mobile_routes_inventory_json={json_out}")
    print(f"mobile_routes_inventory_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_B_MOBILE_ROUTES_INVENTORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
