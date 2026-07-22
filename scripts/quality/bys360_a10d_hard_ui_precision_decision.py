import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(".").resolve()

A10C_JSON = Path("reports/quality/BYS360_A10C_HARD_UI_TECHNICAL_LANGUAGE_PLAN.json")
OUT_JSON = Path("reports/quality/BYS360_A10D_HARD_UI_PRECISION_DECISION.json")
OUT_MD = Path("reports/quality/BYS360_A10D_HARD_UI_PRECISION_DECISION.md")

FALSE_POSITIVE_HINTS = [
    "safe_url_for(",
    ".endpoint",
    " endpoint)",
    "endpoint_ok",
    "data-",
    "name=\"exception_type\"",
    "exception_type",
    "ApiException",
    "api_exception.dart",
    "implements Exception",
    "TimeoutException",
    "SocketException",
    "StackTrace",
    "stackTrace",
    "errorBuilder:",
    "import ",
    "static const",
    "List<String>",
    "application/json",
    "json.stringify",
    "{% for ",
    "{% if ",
    "{{ ",
    "{#",
    "<!--",
    "class=\"",
    "class ",
    "lower.contains",
    "replaceFirst",
    "PlatformDispatcher",
    "Future<void>",
]

SANITIZER_OR_ALLOWED_FILES = [
    "app/static/js/bys360_live_full_overlay_v2_13_0.js",
    "mobile_flutter/bys360_mobile_native/lib/core/theme/mobile_design_system.dart",
    "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
]

REAL_UI_TEXT_PATTERNS = [
    r">\s*[^<]*(traceback|stacktrace|unauthorized_scope|raw error|api error|pytest|ruff|compileall|workflow state)[^<]*\s*<",
    r"['\"]\s*[^'\"]*(traceback|stacktrace|unauthorized_scope|raw error|api error|pytest|ruff|compileall|workflow state)[^'\"]*\s*['\"]",
]

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def looks_false_positive(sample: str, path: str) -> bool:
    s = sample or ""

    if path in SANITIZER_OR_ALLOWED_FILES:
        return True

    return any(hint in s for hint in FALSE_POSITIVE_HINTS)

def looks_real_ui_text(sample: str) -> bool:
    s = sample or ""
    low = s.lower()

    if looks_false_positive(s, ""):
        return False

    for pattern in REAL_UI_TEXT_PATTERNS:
        if re.search(pattern, low, flags=re.I):
            return True

    # Basit HTML text ya da direkt kullanıcı mesajı ihtimali
    if any(term in low for term in [
        "traceback",
        "stacktrace",
        "unauthorized_scope",
        "raw error",
        "api error",
        "workflow state",
        "pytest",
        "ruff",
        "compileall",
    ]):
        # Kod satırı gibi durmuyorsa gerçek UI kabul et
        code_markers = ["=", "=>", "const ", "static ", "import ", "class ", "def ", "function", "{{", "{%", "data-", "href=", "name="]
        if not any(marker in low for marker in code_markers):
            return True

    return False

def main():
    if not A10C_JSON.exists():
        raise SystemExit("A10C raporu bulunamadı. Önce A10C çalışmalı.")

    a10c = read_json(A10C_JSON)

    real_ui = []
    false_positive = []
    review = []

    for item in a10c.get("plan", []):
        path = item.get("path", "")
        for hit in item.get("suggestions", []):
            row = {
                "path": path,
                "line": hit.get("line"),
                "term": hit.get("term"),
                "sample": hit.get("sample"),
                "suggested_message": hit.get("suggested_message"),
            }

            sample = row["sample"] or ""

            if looks_false_positive(sample, path):
                row["decision"] = "false_positive_code_or_sanitizer"
                false_positive.append(row)
            elif looks_real_ui_text(sample):
                row["decision"] = "real_user_facing_text"
                real_ui.append(row)
            else:
                row["decision"] = "manual_review"
                review.append(row)

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10D_HARD_UI_PRECISION_DECISION",
        "mode": "audit_only",
        "source_a10c": str(A10C_JSON),
        "source_hard_ui_file_count": a10c.get("hard_ui_file_count"),
        "source_hard_ui_hit_total": a10c.get("hard_ui_hit_total"),
        "real_user_facing_hit_count": len(real_ui),
        "false_positive_hit_count": len(false_positive),
        "manual_review_hit_count": len(review),
        "real_user_facing_hits": real_ui,
        "false_positive_hits": false_positive[:500],
        "manual_review_hits": review,
        "ok": len(real_ui) == 0 and len(review) == 0,
        "next_action": "Gerçek kullanıcı metni varsa A10E patch; yoksa A10E false-positive allowlist gate.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10D Hard UI Precision Decision",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Özet",
        "",
        f"- Source hard UI file count: {result['source_hard_ui_file_count']}",
        f"- Source hard UI hit total: {result['source_hard_ui_hit_total']}",
        f"- Real user-facing hit count: {result['real_user_facing_hit_count']}",
        f"- False positive hit count: {result['false_positive_hit_count']}",
        f"- Manual review hit count: {result['manual_review_hit_count']}",
        f"- A10D OK: {result['ok']}",
        "",
        "## Gerçek Kullanıcı Metni Bulguları",
        "",
        "```json",
        json.dumps(result["real_user_facing_hits"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Manuel İnceleme Bulguları",
        "",
        "```json",
        json.dumps(result["manual_review_hits"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## False Positive Örnekleri",
        "",
        "```json",
        json.dumps(result["false_positive_hits"][:120], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        "Bu aşama dosya değiştirmez. Kod içi endpoint, ApiException, StackTrace, Jinja değişkeni ve sanitizer ifadeleri kullanıcıya görünen teknik dil sayılmamıştır.",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10D_REPORT_JSON:", OUT_JSON)
    print("A10D_REPORT_MD:", OUT_MD)
    print("A10D_REAL_USER_FACING_HIT_COUNT:", result["real_user_facing_hit_count"])
    print("A10D_FALSE_POSITIVE_HIT_COUNT:", result["false_positive_hit_count"])
    print("A10D_MANUAL_REVIEW_HIT_COUNT:", result["manual_review_hit_count"])
    print("A10D_OK:", result["ok"])

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
