from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter, defaultdict
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

HIGH_RISK_HINTS = (
    "password", "set_password", "check_password_hash", "token", "jwt", "session[",
    "commit(", "rollback(", "db.session.add", "db.session.delete", ".delete(",
    "current_user", "login_user", "logout_user",
)

DB_READ_HINTS = (
    "db.session", ".query", ".filter", ".filter_by", ".join", ".all(", ".first(", ".get(",
)

JSON_HINTS = ("jsonify", "mobile_success", "mobile_error")


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
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    out = []
    for dec in node.decorator_list:
        try:
            out.append(ast.unparse(dec))
        except Exception:
            out.append("")
    return out


def extract_routes(decorators: list[str]) -> list[dict[str, Any]]:
    rows = []
    for dec in decorators:
        if ".route(" not in dec and not dec.startswith("route("):
            continue
        route_match = re.search(r"['\"]([^'\"]+)['\"]", dec)
        route = route_match.group(1) if route_match else dec
        methods = []
        methods_match = re.search(r"methods\s*=\s*\[([^\]]*)\]", dec)
        if methods_match:
            methods = re.findall(r"['\"]([A-Z]+)['\"]", methods_match.group(1))
        rows.append({"route": route, "methods": methods, "decorator": dec})
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
    decorators = decorators_text(node)
    routes = extract_routes(decorators)
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
    json_hits = sorted(h for h in JSON_HINTS if h.lower() in src.lower())

    methods = sorted({m for r in routes for m in r["methods"]})
    has_write_method = any(m in {"POST", "PUT", "PATCH", "DELETE"} for m in methods)
    has_route = bool(routes)

    if not has_route:
        decision = "NOT_ROUTE_HELPER"
        reason = "Route decorator yok; bu aşamada taşınmayacak."
        risk_level = "LOW"
    elif high_risk or has_write_method:
        decision = "DEFER_HIGH_RISK_WRITE_OR_AUTH"
        reason = "Auth/token/password/write işlem riski veya POST/PUT/PATCH/DELETE metodu içeriyor."
        risk_level = "HIGH"
    elif count >= 80:
        decision = "DEFER_LARGE_ROUTE"
        reason = "Büyük route fonksiyonu; ayrı refactor planı gerekir."
        risk_level = "HIGH"
    elif db_read and count > 45:
        decision = "REVIEW_DB_READ_ROUTE"
        reason = "DB okuma içeriyor ve orta boy; smoke testle ayrıca değerlendirilmeli."
        risk_level = "MEDIUM"
    elif domain in {"utility", "dashboard"} and count <= 55:
        decision = "FIRST_SPLIT_CANDIDATE"
        reason = "Küçük ve görece düşük riskli route; ilk bridge split için aday."
        risk_level = "LOW_MEDIUM"
    elif count <= 45 and not high_risk:
        decision = "LOW_RISK_ROUTE_CANDIDATE"
        reason = "Küçük route; domain grubuna göre sonraki aday olabilir."
        risk_level = "MEDIUM"
    else:
        decision = "REVIEW_ROUTE"
        reason = "Route var ancak ilk taşıma için elle değerlendirme gerekir."
        risk_level = "MEDIUM"

    return {
        "name": name,
        "start": start,
        "end": end,
        "lines": count,
        "routes": routes,
        "methods": methods,
        "domain": domain,
        "call_sample": sorted(set(calls))[:80],
        "names_sample": sorted(set(names))[:80],
        "high_risk_hits": high_risk,
        "db_read_hits": db_read,
        "json_hits": json_hits,
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

    print("BYS360_QUALITY_10_10_P11_B1_MOBILE_ROUTES_SPLIT_CANDIDATES_START")
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

    first_candidates = [f for f in route_functions if f["decision"] == "FIRST_SPLIT_CANDIDATE"]
    low_candidates = [f for f in route_functions if f["decision"] == "LOW_RISK_ROUTE_CANDIDATE"]
    review_candidates = [f for f in route_functions if f["decision"] in {"REVIEW_DB_READ_ROUTE", "REVIEW_ROUTE"}]
    deferred = [f for f in route_functions if f["decision"].startswith("DEFER")]

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for f in first_candidates + low_candidates:
        grouped[f["domain"]].append(f)

    # Pick next recommended group. Avoid auth/personnel first.
    group_priority = ["utility", "dashboard", "support", "survey", "communication", "settings"]
    recommended_domain = None
    for domain in group_priority:
        if grouped.get(domain):
            recommended_domain = domain
            break

    recommendation = {
        "recommended_domain": recommended_domain,
        "recommended_functions": grouped.get(recommended_domain, []) if recommended_domain else [],
        "reason": (
            "İlk gerçek split için auth/personnel/write işlemlerinden uzak, küçük route grubu tercih edilmeli."
            if recommended_domain else
            "Düşük riskli route grubu bulunamadı; gerçek split yapılmamalı."
        ),
        "next_step": "P11-B2 düşük riskli route grubu için bridge split patch hazırlanabilir." if recommended_domain else "Önce manuel inceleme gerekir.",
    }

    report = {
        "target_file": TARGET_REL,
        "line_count": len(lines),
        "function_count": len(functions),
        "route_function_count": len(route_functions),
        "by_decision": dict(by_decision.most_common()),
        "route_domain_summary": dict(by_domain.most_common()),
        "route_risk_summary": dict(by_risk.most_common()),
        "first_split_candidates": first_candidates,
        "low_risk_candidates": low_candidates,
        "review_candidates": review_candidates,
        "deferred_candidates": deferred,
        "grouped_candidates": {k: v for k, v in grouped.items()},
        "recommendation": recommendation,
        "safety_strategy": [
            "Auth, token, password ve personel oluşturma endpointleri ilk split kapsamında taşınmamalıdır.",
            "İlk gerçek split için sadece küçük GET/utility/dashboard tarzı endpoint grubu seçilmelidir.",
            "URL path ve JSON cevap formatı birebir korunmalıdır.",
            "Mevcut blueprint nesnesi korunmalı; yeni dosyalar aynı blueprint'e route register etmelidir.",
            "Her taşıma sonrası compileall, audit, mobil API smoke ve Flutter smoke test çalıştırılmalıdır.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_b1_mobile_routes_split_candidates_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_b1_mobile_routes_split_candidates_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-B1 Mobile Routes Split Candidate Raporu")
    md.append("")
    md.append(f"- Dosya: `{TARGET_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Fonksiyon sayısı: {len(functions)}")
    md.append(f"- Route fonksiyon sayısı: {len(route_functions)}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for k, v in by_decision.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Route Risk Özeti")
    md.append("")
    for k, v in by_risk.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Önerilen İlk Domain")
    md.append("")
    md.append(f"- Domain: `{recommended_domain or '-'}`")
    md.append(f"- Gerekçe: {recommendation['reason']}")
    md.append("")
    if recommendation["recommended_functions"]:
        md.append("Önerilen fonksiyonlar:")
        for f in recommendation["recommended_functions"]:
            route = ", ".join(r["route"] for r in f["routes"])
            md.append(f"- `{f['name']}` satır {f['start']}-{f['end']} ({f['lines']} satır), route={route}")
    else:
        md.append("- Önerilen fonksiyon yok.")
    md.append("")
    md.append("## First Split Candidates")
    md.append("")
    for f in first_candidates:
        route = ", ".join(r["route"] for r in f["routes"])
        md.append(f"- `{f['name']}` ({f['domain']}) satır {f['start']}-{f['end']} ({f['lines']}), route={route}")
    md.append("")
    md.append("## Low Risk Candidates")
    md.append("")
    for f in low_candidates[:80]:
        route = ", ".join(r["route"] for r in f["routes"])
        md.append(f"- `{f['name']}` ({f['domain']}) satır {f['start']}-{f['end']} ({f['lines']}), route={route}")
    md.append("")
    md.append("## Ertelenen Yüksek Riskliler")
    md.append("")
    for f in deferred:
        route = ", ".join(r["route"] for r in f["routes"])
        md.append(f"- `{f['name']}` ({f['domain']}) satır {f['start']}-{f['end']} ({f['lines']}), route={route}, risk={', '.join(f['high_risk_hits']) or '-'}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={len(lines)}")
    print(f"function_count={len(functions)}")
    print(f"route_function_count={len(route_functions)}")
    print("BYS360_QUALITY_10_10_P11_B1_DECISION_SUMMARY")
    for k, v in by_decision.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_B1_ROUTE_RISK_SUMMARY")
    for k, v in by_risk.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_B1_FIRST_SPLIT_CANDIDATES")
    for f in first_candidates[:args.limit]:
        route = ",".join(r["route"] for r in f["routes"])
        print(f"{f['lines']:>4} | {f['domain']} | {f['start']}-{f['end']} | {f['name']} | route={route}")
    print("BYS360_QUALITY_10_10_P11_B1_LOW_RISK_CANDIDATES")
    for f in low_candidates[:args.limit]:
        route = ",".join(r["route"] for r in f["routes"])
        print(f"{f['lines']:>4} | {f['domain']} | {f['start']}-{f['end']} | {f['name']} | route={route}")
    print("BYS360_QUALITY_10_10_P11_B1_RECOMMENDATION")
    print(f"recommended_domain={recommended_domain or '-'}")
    if recommendation["recommended_functions"]:
        print("recommended_functions=" + ",".join(f["name"] for f in recommendation["recommended_functions"]))
    else:
        print("recommended_functions=-")
    print(f"split_candidates_json={json_out}")
    print(f"split_candidates_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_B1_MOBILE_ROUTES_SPLIT_CANDIDATES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
