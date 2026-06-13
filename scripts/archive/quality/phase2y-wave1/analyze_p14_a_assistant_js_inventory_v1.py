from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TARGET_REL = "app/static/js/bys360_assistant_module.js"


RISK_KEYWORDS = {
    "network": ["fetch(", "XMLHttpRequest", "axios.", "$.ajax", "navigator.sendBeacon"],
    "storage": ["localStorage", "sessionStorage", "indexedDB", "document.cookie"],
    "dom_write": ["innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"],
    "dom_select": ["querySelector", "querySelectorAll", "getElementById", "getElementsByClassName"],
    "event": ["addEventListener", "removeEventListener", "onclick", "onchange", "onsubmit"],
    "timer": ["setTimeout", "setInterval", "requestAnimationFrame"],
    "security": ["eval(", "new Function", "postMessage", "crypto.", "atob(", "btoa("],
    "assistant": ["assistant", "asistan", "ai", "chat", "knowledge", "screen", "context", "intent"],
    "api": ["/api/", "endpoint", "csrf", "token", "Authorization", "credentials"],
}

DOMAIN_HINTS = {
    "boot": ["init", "bootstrap", "DOMContentLoaded", "load", "ready"],
    "ui_shell": ["panel", "drawer", "modal", "toggle", "open", "close", "resize", "position"],
    "chat": ["chat", "message", "conversation", "send", "ask", "reply", "typing"],
    "screen_context": ["screen", "page", "context", "route", "menu", "breadcrumb", "dom"],
    "knowledge": ["knowledge", "teaching", "guide", "help", "rehber", "bilgi"],
    "security": ["csrf", "token", "auth", "permission", "role", "yetki"],
    "network": ["fetch", "api", "endpoint", "request", "response"],
    "storage": ["localStorage", "sessionStorage", "cache", "state"],
    "feedback": ["feedback", "rating", "thumb", "vote"],
    "notification": ["notification", "reminder", "alert", "toast"],
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def line_no_from_pos(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def extract_comment_sections(lines: list[str]) -> list[dict[str, Any]]:
    sections = []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            clean = re.sub(r"^(/\*+|\*+|//+)\s*", "", stripped).strip(" */")
            if len(clean) >= 6 and (
                clean.isupper()
                or clean.startswith("BYS360")
                or "===" in stripped
                or "---" in stripped
                or "P14" in clean
                or "assistant" in clean.lower()
                or "asistan" in clean.lower()
            ):
                sections.append({"line": i, "text": clean[:220]})
    return sections


def extract_functions(text: str) -> list[dict[str, Any]]:
    patterns = [
        ("function_decl", re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", re.MULTILINE)),
        ("const_arrow", re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>", re.MULTILINE)),
        ("const_function", re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?function\b", re.MULTILINE)),
        ("method_like", re.compile(r"^\s{0,8}([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{", re.MULTILINE)),
    ]

    functions = []
    seen = set()
    for kind, pattern in patterns:
        for m in pattern.finditer(text):
            name = m.group(1)
            line = line_no_from_pos(text, m.start())
            key = (name, line)
            if key in seen:
                continue
            seen.add(key)
            functions.append({
                "name": name,
                "line": line,
                "kind": kind,
                "domain": classify_domain(name),
            })
    return sorted(functions, key=lambda x: x["line"])


def extract_classes(text: str) -> list[dict[str, Any]]:
    rows = []
    for m in re.finditer(r"\bclass\s+([A-Za-z_$][\w$]*)", text):
        rows.append({
            "name": m.group(1),
            "line": line_no_from_pos(text, m.start()),
            "domain": classify_domain(m.group(1)),
        })
    return rows


def extract_event_listeners(text: str) -> list[dict[str, Any]]:
    rows = []
    pattern = re.compile(r"\.addEventListener\s*\(\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
    for m in pattern.finditer(text):
        rows.append({
            "event": m.group(1),
            "line": line_no_from_pos(text, m.start()),
            "snippet": get_line(text, line_no_from_pos(text, m.start())).strip()[:220],
        })
    return rows


def extract_strings(text: str) -> list[dict[str, Any]]:
    rows = []
    string_re = re.compile(r"(['\"])(.*?)\1", re.DOTALL)
    for m in string_re.finditer(text):
        value = m.group(2)
        if len(value) > 260:
            continue
        if (
            value.startswith("/")
            or "/api/" in value
            or value.startswith("#")
            or value.startswith(".")
            or "assistant" in value.lower()
            or "asistan" in value.lower()
            or "csrf" in value.lower()
            or "token" in value.lower()
        ):
            rows.append({
                "line": line_no_from_pos(text, m.start()),
                "value": value,
                "kind": classify_string(value),
            })
    return rows


def classify_string(value: str) -> str:
    low = value.lower()
    if value.startswith("/"):
        return "path_or_endpoint"
    if value.startswith("#") or value.startswith("."):
        return "selector"
    if "csrf" in low or "token" in low:
        return "security"
    if "assistant" in low or "asistan" in low:
        return "assistant"
    return "other"


def get_line(text: str, line_no: int) -> str:
    lines = text.splitlines()
    if 1 <= line_no <= len(lines):
        return lines[line_no - 1]
    return ""


def classify_domain(name_or_text: str) -> str:
    low = name_or_text.lower()
    scores = Counter()
    for domain, hints in DOMAIN_HINTS.items():
        for hint in hints:
            if hint.lower() in low:
                scores[domain] += 1
    if scores:
        return scores.most_common(1)[0][0]
    return "general"


def extract_fetch_calls(text: str) -> list[dict[str, Any]]:
    rows = []
    for m in re.finditer(r"\bfetch\s*\(([^,\n)]+)", text):
        line = line_no_from_pos(text, m.start())
        rows.append({
            "line": line,
            "target": m.group(1).strip()[:180],
            "snippet": get_line(text, line).strip()[:240],
        })
    return rows


def count_keyword_hits(lines: list[str]) -> list[dict[str, Any]]:
    rows = []
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        hits = []
        for category, words in RISK_KEYWORDS.items():
            for word in words:
                if word.lower() in low:
                    hits.append(category)
                    break
        if hits:
            rows.append({
                "line": i,
                "categories": sorted(set(hits)),
                "snippet": line.strip()[:240],
            })
    return rows


def estimate_function_ranges(functions: list[dict[str, Any]], total_lines: int) -> list[dict[str, Any]]:
    ranged = []
    for idx, fn in enumerate(functions):
        start = int(fn["line"])
        next_start = int(functions[idx + 1]["line"]) if idx + 1 < len(functions) else total_lines + 1
        estimated_lines = max(1, next_start - start)
        item = dict(fn)
        item["estimated_lines_until_next_function"] = estimated_lines
        if estimated_lines >= 180:
            item["size_bucket"] = "VERY_LARGE_REVIEW"
        elif estimated_lines >= 80:
            item["size_bucket"] = "LARGE_REVIEW"
        elif estimated_lines >= 35:
            item["size_bucket"] = "MEDIUM"
        else:
            item["size_bucket"] = "SMALL"
        ranged.append(item)
    return ranged


def make_split_recommendation(functions: list[dict[str, Any]], keyword_hits: list[dict[str, Any]], line_count: int) -> dict[str, Any]:
    by_domain = Counter(fn["domain"] for fn in functions)
    risky_lines = Counter(cat for hit in keyword_hits for cat in hit["categories"])

    return {
        "decision": "INVENTORY_ONLY_NO_SPLIT",
        "reason": "Bu aşamada kod taşınmaz. Asistan JS ekran zekâsı, DOM davranışı, API çağrıları ve kullanıcı yönlendirme akışlarını birlikte içeriyor.",
        "line_count": line_count,
        "function_domain_summary": dict(by_domain.most_common()),
        "risk_keyword_summary": dict(risky_lines.most_common()),
        "recommended_next": "P14-B split candidate decision report; sadece en düşük riskli saf yardımcı fonksiyon kümeleri aday gösterilmeli.",
        "do_not_touch_yet": [
            "fetch/API çağrıları",
            "CSRF/token/oturum mantığı",
            "ekran bağlamı çıkarımı",
            "menü/route yönlendirme haritası",
            "chat mesaj gönderme/yanıt alma akışı",
            "DOM yazma ve panel aç/kapat davranışları",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=240)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_QUALITY_10_10_P14_A_ASSISTANT_JS_INVENTORY_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = read_text(target)
    lines = text.splitlines()
    line_count = len(lines)

    comment_sections = extract_comment_sections(lines)
    classes = extract_classes(text)
    functions = estimate_function_ranges(extract_functions(text), line_count)
    events = extract_event_listeners(text)
    strings = extract_strings(text)
    fetch_calls = extract_fetch_calls(text)
    keyword_hits = count_keyword_hits(lines)

    by_function_domain = Counter(fn["domain"] for fn in functions)
    by_function_size = Counter(fn["size_bucket"] for fn in functions)
    by_event = Counter(event["event"] for event in events)
    by_string_kind = Counter(item["kind"] for item in strings)
    by_keyword_category = Counter(cat for hit in keyword_hits for cat in hit["categories"])

    large_functions = [fn for fn in functions if fn["size_bucket"] in {"LARGE_REVIEW", "VERY_LARGE_REVIEW"}]
    network_or_security_lines = [
        hit for hit in keyword_hits
        if any(cat in {"network", "security", "api", "storage"} for cat in hit["categories"])
    ]

    split_recommendation = make_split_recommendation(functions, keyword_hits, line_count)

    result = {
        "target_file": TARGET_REL,
        "line_count": line_count,
        "comment_section_count": len(comment_sections),
        "class_count": len(classes),
        "function_count": len(functions),
        "event_listener_count": len(events),
        "fetch_call_count": len(fetch_calls),
        "interesting_string_count": len(strings),
        "keyword_hit_count": len(keyword_hits),
        "function_domain_summary": dict(by_function_domain.most_common()),
        "function_size_summary": dict(by_function_size.most_common()),
        "event_summary": dict(by_event.most_common()),
        "string_kind_summary": dict(by_string_kind.most_common()),
        "keyword_category_summary": dict(by_keyword_category.most_common()),
        "comment_sections": comment_sections,
        "classes": classes,
        "functions": functions,
        "large_functions": large_functions,
        "event_listeners": events,
        "fetch_calls": fetch_calls,
        "interesting_strings": strings,
        "network_or_security_lines": network_or_security_lines,
        "split_recommendation": split_recommendation,
        "safety_strategy": [
            "P14-A kod değiştirmez.",
            "Asistan JS için ilk hedef parçalama değil, davranış haritası çıkarmaktır.",
            "P14-B olmadan fetch/API, CSRF/token, DOM yazma, ekran bağlamı ve chat akışları taşınmamalıdır.",
            "Parçalama yapılacaksa önce saf yardımcı fonksiyonlar veya statik veri haritaları aday gösterilmelidir.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p14_a_assistant_js_inventory_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p14_a_assistant_js_inventory_v1.md"
    json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P14-A Assistant JS Inventory")
    md.append("")
    md.append(f"- Dosya: `{TARGET_REL}`")
    md.append(f"- Satır sayısı: {line_count}")
    md.append(f"- Fonksiyon sayısı: {len(functions)}")
    md.append(f"- Büyük fonksiyon adayı: {len(large_functions)}")
    md.append(f"- Event listener sayısı: {len(events)}")
    md.append(f"- Fetch/API çağrısı: {len(fetch_calls)}")
    md.append("")
    md.append("## Fonksiyon Domain Özeti")
    md.append("")
    for key, count in by_function_domain.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Risk/Kullanım Kategorileri")
    md.append("")
    for key, count in by_keyword_category.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Büyük Fonksiyon Adayları")
    md.append("")
    if large_functions:
        for fn in large_functions[:80]:
            md.append(f"- `{fn['name']}` line {fn['line']} — {fn['domain']} — {fn['estimated_lines_until_next_function']} satır tahmini — {fn['size_bucket']}")
    else:
        md.append("- Büyük fonksiyon adayı bulunmadı.")
    md.append("")
    md.append("## Fetch/API Çağrıları")
    md.append("")
    if fetch_calls:
        for item in fetch_calls[:80]:
            md.append(f"- line {item['line']}: `{item['snippet']}`")
    else:
        md.append("- Fetch çağrısı bulunmadı.")
    md.append("")
    md.append("## Karar")
    md.append("")
    md.append(f"- {split_recommendation['decision']}: {split_recommendation['reason']}")
    md.append(f"- Sonraki adım: {split_recommendation['recommended_next']}")
    md.append("")
    md.append("## Güvenlik Stratejisi")
    md.append("")
    for item in result["safety_strategy"]:
        md.append(f"- {item}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={line_count}")
    print(f"function_count={len(functions)}")
    print(f"large_function_count={len(large_functions)}")
    print(f"event_listener_count={len(events)}")
    print(f"fetch_call_count={len(fetch_calls)}")
    print(f"interesting_string_count={len(strings)}")
    print("BYS360_QUALITY_10_10_P14_A_FUNCTION_DOMAIN_SUMMARY")
    for key, count in by_function_domain.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P14_A_FUNCTION_SIZE_SUMMARY")
    for key, count in by_function_size.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P14_A_KEYWORD_CATEGORY_SUMMARY")
    for key, count in by_keyword_category.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P14_A_LARGE_FUNCTIONS")
    for fn in large_functions[:args.limit]:
        print(f"{fn['line']:>5} | {fn['estimated_lines_until_next_function']:>4} | {fn['size_bucket']} | {fn['domain']} | {fn['name']}")
    print("BYS360_QUALITY_10_10_P14_A_FETCH_CALLS")
    for item in fetch_calls[:args.limit]:
        print(f"{item['line']:>5} | {item['target']} | {item['snippet']}")
    print("BYS360_QUALITY_10_10_P14_A_DECISION")
    print(f"decision={split_recommendation['decision']}")
    print(f"recommended_next={split_recommendation['recommended_next']}")
    print(f"assistant_js_inventory_json={json_out}")
    print(f"assistant_js_inventory_md={md_out}")
    print("BYS360_QUALITY_10_10_P14_A_ASSISTANT_JS_INVENTORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
