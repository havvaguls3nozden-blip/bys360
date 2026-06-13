from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_REL = "app/static/js/bys360_assistant_module.js"
P14_A_REL = "reports/quality/bys360_quality_10_10_p14_a_assistant_js_inventory_v1.json"

RESERVED_OR_FAKE_NAMES = {
    "if", "for", "while", "switch", "catch", "setTimeout", "setInterval",
    "addEventListener", "then", "map", "filter", "forEach", "reduce",
}

RISK_PATTERNS = {
    "fetch_api": [r"\bfetch\s*\(", r"/api/", r"XMLHttpRequest", r"axios\.", r"\$\.ajax"],
    "csrf_auth": [r"csrf", r"token", r"Authorization", r"credentials", r"auth", r"permission", r"role", r"yetki"],
    "dom_write": [r"\.innerHTML\b", r"\.outerHTML\b", r"insertAdjacentHTML", r"document\.write"],
    "dom_read": [r"querySelector", r"querySelectorAll", r"getElementById", r"closest\(", r"classList"],
    "event": [r"addEventListener", r"removeEventListener", r"\bonclick\b", r"\bonchange\b", r"\bonsubmit\b"],
    "storage": [r"localStorage", r"sessionStorage", r"indexedDB", r"document\.cookie"],
    "timer": [r"setTimeout", r"setInterval", r"requestAnimationFrame"],
    "security_dynamic": [r"\beval\s*\(", r"new\s+Function", r"postMessage", r"\batob\s*\(", r"\bbtoa\s*\("],
    "assistant_flow": [r"assistant", r"asistan", r"chat", r"intent", r"context", r"screen", r"route", r"menu", r"knowledge"],
}

DOMAIN_HINTS = {
    "text_helper": ["escape", "text", "normalize", "sanitize", "slug", "trim", "format", "label"],
    "dom_helper": ["el", "node", "attr", "class", "selector", "panel", "button", "modal"],
    "route_helper": ["path", "route", "url", "home", "href", "endpoint"],
    "assistant_flow": ["assistant", "asistan", "chat", "ask", "answer", "intent", "message"],
    "screen_context": ["screen", "context", "page", "menu", "breadcrumb", "collectFacts", "facts"],
    "network": ["fetch", "api", "request", "response", "weather", "summary"],
    "storage": ["cache", "storage", "state", "remember"],
    "boot": ["init", "boot", "ready", "load", "mount"],
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception as exc:
        print(f"BYS360_P14_B_JSON_READ_WARN path={path} error={exc}")
        return None


def line_from_pos(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def strip_js_comments_and_strings_for_scan(text: str) -> str:
    # Preserve length roughly for scanning, not for exact parsing.
    out = []
    i = 0
    n = len(text)
    state = "code"
    quote = ""
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if state == "code":
            if ch == "/" and nxt == "/":
                state = "line_comment"
                out.append(" ")
                out.append(" ")
                i += 2
                continue
            if ch == "/" and nxt == "*":
                state = "block_comment"
                out.append(" ")
                out.append(" ")
                i += 2
                continue
            if ch in ("'", '"', "`"):
                state = "string"
                quote = ch
                out.append(" ")
                i += 1
                continue
            out.append(ch)
            i += 1
            continue

        if state == "line_comment":
            if ch == "\n":
                state = "code"
                out.append("\n")
            else:
                out.append(" ")
            i += 1
            continue

        if state == "block_comment":
            if ch == "*" and nxt == "/":
                state = "code"
                out.append(" ")
                out.append(" ")
                i += 2
            else:
                out.append("\n" if ch == "\n" else " ")
                i += 1
            continue

        if state == "string":
            if ch == "\\":
                out.append(" ")
                if i + 1 < n:
                    out.append(" ")
                    i += 2
                else:
                    i += 1
                continue
            if ch == quote:
                state = "code"
                quote = ""
                out.append(" ")
                i += 1
                continue
            out.append("\n" if ch == "\n" else " ")
            i += 1
            continue

    return "".join(out)


def find_matching_brace(text: str, open_pos: int) -> int | None:
    # Brace matcher with string/comment awareness.
    i = open_pos
    n = len(text)
    depth = 0
    state = "code"
    quote = ""

    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if state == "code":
            if ch == "/" and nxt == "/":
                state = "line_comment"
                i += 2
                continue
            if ch == "/" and nxt == "*":
                state = "block_comment"
                i += 2
                continue
            if ch in ("'", '"', "`"):
                state = "string"
                quote = ch
                i += 1
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
            continue

        if state == "line_comment":
            if ch == "\n":
                state = "code"
            i += 1
            continue

        if state == "block_comment":
            if ch == "*" and nxt == "/":
                state = "code"
                i += 2
            else:
                i += 1
            continue

        if state == "string":
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                state = "code"
                quote = ""
            i += 1
            continue

    return None


def find_open_brace_after(text: str, start_pos: int, max_scan: int = 600) -> int | None:
    end = min(len(text), start_pos + max_scan)
    for i in range(start_pos, end):
        if text[i] == "{":
            return i
        if text[i] == ";":
            return None
    return None


def extract_real_functions(text: str) -> list[dict[str, Any]]:
    patterns = [
        ("function_decl", re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", re.MULTILINE)),
        ("var_function", re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?function\b", re.MULTILINE)),
        ("var_arrow", re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>", re.MULTILINE)),
    ]

    funcs = []
    seen = set()

    for kind, pattern in patterns:
        for m in pattern.finditer(text):
            name = m.group(1)
            if name in RESERVED_OR_FAKE_NAMES:
                continue
            open_pos = find_open_brace_after(text, m.end())
            if open_pos is None:
                continue
            close_pos = find_matching_brace(text, open_pos)
            if close_pos is None:
                continue

            start_line = line_from_pos(text, m.start())
            end_line = line_from_pos(text, close_pos)
            key = (name, start_line)
            if key in seen:
                continue
            seen.add(key)

            body = text[open_pos:close_pos + 1]
            funcs.append({
                "name": name,
                "kind": kind,
                "start_line": start_line,
                "end_line": end_line,
                "line_count": max(1, end_line - start_line + 1),
                "domain": classify_domain(name + "\n" + body[:1200]),
                "risk_hits": detect_risks(body),
                "called_functions": extract_called_names(body),
                "body_preview": body[:300],
            })

    return sorted(funcs, key=lambda item: item["start_line"])


def classify_domain(text: str) -> str:
    low = text.lower()
    scores = Counter()
    for domain, hints in DOMAIN_HINTS.items():
        for hint in hints:
            if hint.lower() in low:
                scores[domain] += 1
    return scores.most_common(1)[0][0] if scores else "general"


def detect_risks(body: str) -> list[str]:
    low_body = body
    hits = []
    for category, patterns in RISK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, low_body, flags=re.IGNORECASE):
                hits.append(category)
                break
    return sorted(set(hits))


def extract_called_names(body: str) -> list[str]:
    calls = re.findall(r"\b([A-Za-z_$][\w$]*)\s*\(", body)
    ignore = {
        "if", "for", "while", "switch", "catch", "return", "function",
        "setTimeout", "setInterval", "fetch", "String", "Number", "Boolean",
        "Array", "Object", "JSON", "Math", "Date", "RegExp",
    }
    return sorted({c for c in calls if c not in ignore})[:80]


def classify_split_decision(fn: dict[str, Any]) -> tuple[str, str, str]:
    risks = set(fn["risk_hits"])
    line_count = int(fn["line_count"])
    domain = str(fn["domain"])
    name = str(fn["name"])

    high_risk = {"fetch_api", "csrf_auth", "dom_write", "event", "security_dynamic", "assistant_flow"}
    medium_risk = {"dom_read", "storage", "timer"}

    if risks & high_risk:
        return (
            "DEFER_COUPLED_ASSISTANT_OR_UI_FLOW",
            "HIGH",
            "API/CSRF/DOM yazma/event/asistan akışı ile bağlı; ilk split adayı olmamalı.",
        )

    if line_count >= 120:
        return (
            "DEFER_LARGE_HELPER_REVIEW",
            "MEDIUM_HIGH",
            "Büyük yardımcı blok; test kapsamı olmadan taşınmamalı.",
        )

    if risks & medium_risk:
        return (
            "REVIEW_MEDIUM_RISK_HELPER",
            "MEDIUM",
            "DOM okuma/storage/timer içeriyor; kullanıcı davranışına etkisi elle kontrol edilmeli.",
        )

    if line_count <= 80 and domain in {"text_helper", "general", "route_helper"}:
        return (
            "LOW_RISK_HELPER_CANDIDATE",
            "LOW_MEDIUM",
            "Küçük ve riskli API/DOM yazma/event içermeyen yardımcı fonksiyon olabilir.",
        )

    return (
        "REVIEW_HELPER_CANDIDATE",
        "MEDIUM",
        "Risk düşük görünüyor ancak bağlam doğrulaması gerekir.",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=240)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL
    p14_a = load_json(project_root / P14_A_REL)

    print("BYS360_QUALITY_10_10_P14_B_ASSISTANT_JS_SPLIT_DECISION_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = read_text(target)
    line_count = len(text.splitlines())
    funcs = extract_real_functions(text)

    enriched = []
    for fn in funcs:
        decision, risk, reason = classify_split_decision(fn)
        item = dict(fn)
        item["decision"] = decision
        item["risk"] = risk
        item["reason"] = reason
        enriched.append(item)

    by_decision = Counter(item["decision"] for item in enriched)
    by_domain = Counter(item["domain"] for item in enriched)
    by_risk = Counter(item["risk"] for item in enriched)

    low_candidates = [item for item in enriched if item["decision"] == "LOW_RISK_HELPER_CANDIDATE"]
    review_candidates = [item for item in enriched if item["decision"] in {"REVIEW_HELPER_CANDIDATE", "REVIEW_MEDIUM_RISK_HELPER"}]
    deferred = [item for item in enriched if item["decision"].startswith("DEFER")]

    # Keep P14-B as decision report only. Recommend P14-C only if enough low-risk candidates exist.
    if len(low_candidates) >= 3:
        next_decision = {
            "decision": "P14_C_LOW_RISK_HELPER_DRYRUN_PLAN",
            "reason": "Birkaç düşük riskli yardımcı fonksiyon var; yine de önce dry-run taşıma planı üretmek gerekir.",
            "recommended_functions": [item["name"] for item in low_candidates[:12]],
        }
    else:
        next_decision = {
            "decision": "KEEP_IN_PLACE_NO_SPLIT_YET",
            "reason": "Düşük riskli aday sayısı sınırlı; dosyayı parçalamadan önce test/smoke ve fonksiyon bağımlılıkları daha net çıkarılmalı.",
            "recommended_functions": [],
        }

    result = {
        "target_file": TARGET_REL,
        "line_count": line_count,
        "p14_a_summary": {
            "function_count_p14_a": (p14_a or {}).get("function_count"),
            "large_function_count_p14_a": (p14_a or {}).get("large_function_count"),
            "fetch_call_count_p14_a": (p14_a or {}).get("fetch_call_count"),
        },
        "real_named_function_count": len(enriched),
        "decision_summary": dict(by_decision.most_common()),
        "domain_summary": dict(by_domain.most_common()),
        "risk_summary": dict(by_risk.most_common()),
        "low_risk_helper_candidates": low_candidates,
        "review_candidates": review_candidates,
        "deferred_candidates": deferred,
        "all_functions": enriched,
        "next_decision": next_decision,
        "safety_strategy": [
            "P14-B kod değiştirmez.",
            "P14-A’daki if/for/setTimeout gibi sahte fonksiyon kayıtları karar dışında tutulur.",
            "API, CSRF/token, DOM yazma, event listener ve asistan/chat akışı ilk split kapsamına alınmaz.",
            "Düşük riskli yardımcı fonksiyonlar bile P14-C dry-run planı olmadan taşınmaz.",
            "Asistan JS kullanıcı yönlendirme ve ekran zekâsı taşıdığı için her adım sonrası tarayıcı smoke test gerekir.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p14_b_assistant_js_split_decision_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p14_b_assistant_js_split_decision_v1.md"
    json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P14-B Assistant JS Split Decision")
    md.append("")
    md.append(f"- Dosya: `{TARGET_REL}`")
    md.append(f"- Satır sayısı: {line_count}")
    md.append(f"- Gerçek isimli fonksiyon sayısı: {len(enriched)}")
    md.append(f"- Düşük riskli yardımcı aday: {len(low_candidates)}")
    md.append(f"- İnceleme adayı: {len(review_candidates)}")
    md.append(f"- Ertelenen/bağlı akış: {len(deferred)}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for key, count in by_decision.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Düşük Riskli Yardımcı Adaylar")
    md.append("")
    if low_candidates:
        for item in low_candidates[:80]:
            md.append(f"- `{item['name']}` line {item['start_line']}-{item['end_line']} ({item['line_count']} satır), domain={item['domain']}, risk={item['risk']}")
    else:
        md.append("- Düşük riskli aday bulunmadı.")
    md.append("")
    md.append("## Ertelenen Kritik/Bağlı Akışlar")
    md.append("")
    for item in deferred[:120]:
        md.append(f"- `{item['name']}` line {item['start_line']}-{item['end_line']} ({item['line_count']} satır), risk_hits={','.join(item['risk_hits'])}")
    md.append("")
    md.append("## Sonraki Karar")
    md.append("")
    md.append(f"- {next_decision['decision']}: {next_decision['reason']}")
    if next_decision["recommended_functions"]:
        md.append(f"- Önerilen adaylar: {', '.join(next_decision['recommended_functions'])}")
    md.append("")
    md.append("## Güvenlik Stratejisi")
    md.append("")
    for item in result["safety_strategy"]:
        md.append(f"- {item}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={line_count}")
    print(f"real_named_function_count={len(enriched)}")
    print(f"low_risk_helper_candidate_count={len(low_candidates)}")
    print(f"review_candidate_count={len(review_candidates)}")
    print(f"deferred_candidate_count={len(deferred)}")
    print("BYS360_QUALITY_10_10_P14_B_DECISION_SUMMARY")
    for key, count in by_decision.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P14_B_DOMAIN_SUMMARY")
    for key, count in by_domain.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P14_B_LOW_RISK_HELPER_CANDIDATES")
    for item in low_candidates[:args.limit]:
        print(f"{item['start_line']:>5}-{item['end_line']:<5} | {item['line_count']:>4} | {item['domain']} | {item['name']}")
    print("BYS360_QUALITY_10_10_P14_B_DEFERRED_CANDIDATES")
    for item in deferred[:args.limit]:
        print(f"{item['start_line']:>5}-{item['end_line']:<5} | {item['line_count']:>4} | {item['domain']} | {item['name']} | risks={','.join(item['risk_hits'])}")
    print("BYS360_QUALITY_10_10_P14_B_NEXT_DECISION")
    print(f"decision={next_decision['decision']}")
    print(f"reason={next_decision['reason']}")
    if next_decision["recommended_functions"]:
        print("recommended_functions=" + ",".join(next_decision["recommended_functions"]))
    else:
        print("recommended_functions=-")
    print(f"assistant_js_split_decision_json={json_out}")
    print(f"assistant_js_split_decision_md={md_out}")
    print("BYS360_QUALITY_10_10_P14_B_ASSISTANT_JS_SPLIT_DECISION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
