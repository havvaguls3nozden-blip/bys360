from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"

S0B_JSON = QUALITY / "BYS360_S0B_SECRET_SIGNAL_CLASSIFICATION_AUDIT.json"

OUT_JSON = QUALITY / "BYS360_S0B2_SECRET_RISK_DECISION_MATRIX.json"
OUT_MD = QUALITY / "BYS360_S0B2_SECRET_RISK_DECISION_MATRIX.md"

SECRET_TERMS = [
    "SECRET_KEY",
    "TCKN_ENCRYPTION_KEY",
    "DATABASE_URL",
    "DB_PASSWORD",
    "POSTGRES_PASSWORD",
    "MAIL_PASSWORD",
    "MAIL_USERNAME",
    "SENTRY_DSN",
    "INSTAGRAM_ACCESS_TOKEN",
    "FLASK_SECRET",
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc)}


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""


def run_cmd(cmd, timeout=300):
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="ignore",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=timeout,
        )
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": proc.returncode,
            "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-12000:],
        }
    except Exception as exc:
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 127,
            "combined_tail": str(exc),
        }


def parse_pytest_summary(text: str) -> dict:
    summary = {}
    pattern = r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warning|warnings)\b"
    for num, key in re.findall(pattern, text or "", flags=re.IGNORECASE):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)

    for key in ["failed", "passed", "errors", "skipped", "deselected", "warnings"]:
        summary.setdefault(key, 0)

    return summary


def get_line(path: Path, line_no: int) -> str:
    text = read_text_safe(path)
    lines = text.splitlines()
    if 1 <= line_no <= len(lines):
        return lines[line_no - 1]
    return ""


def redacted_value_shape(value: str) -> dict:
    raw = value.strip().strip('"').strip("'")
    low = raw.lower()

    placeholders = [
        "changeme",
        "change_me",
        "replace",
        "example",
        "placeholder",
        "todo",
        "buraya",
        "xxx",
        "your_",
        "none",
        "null",
        "false",
        "true",
        "test",
        "dummy",
        "dev",
        "local",
        "sqlite",
        "memory",
    ]

    has_value = bool(raw)
    looks_placeholder = any(x in low for x in placeholders)
    looks_env_ref = any(x in raw for x in ["os.getenv", "os.environ", "environ.get", "current_app.config", "config.get"])
    looks_url = bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw))
    looks_jinja_or_format = "{{" in raw or "}}" in raw or "{" in raw or "}" in raw

    length = len(raw)
    if not raw:
        bucket = "empty"
    elif length <= 8:
        bucket = "1-8"
    elif length <= 20:
        bucket = "9-20"
    elif length <= 40:
        bucket = "21-40"
    elif length <= 80:
        bucket = "41-80"
    else:
        bucket = "80+"

    has_mixed = bool(re.search(r"[A-Z]", raw)) and bool(re.search(r"[a-z]", raw))
    has_digit = bool(re.search(r"\d", raw))
    has_symbol = bool(re.search(r"[^A-Za-z0-9_:/@.\-]", raw))
    looks_secretish = length >= 24 and (has_mixed or has_digit or has_symbol) and not looks_placeholder and not looks_env_ref

    return {
        "has_value": has_value,
        "length_bucket": bucket,
        "looks_placeholder": looks_placeholder,
        "looks_env_ref": looks_env_ref,
        "looks_url": looks_url,
        "looks_jinja_or_format": looks_jinja_or_format,
        "looks_secretish": looks_secretish,
    }


def classify_expression_shape(line: str, term: str) -> dict:
    stripped = line.strip()

    result = {
        "expression_kind": "unknown",
        "value_shape": redacted_value_shape(""),
        "is_dict_key_or_schema": False,
        "is_list_or_tuple_reference": False,
        "is_env_lookup": False,
        "is_test_or_placeholder": False,
    }

    if re.search(rf"['\"]{re.escape(term)}['\"]\s*:", stripped):
        result["expression_kind"] = "dict_key_or_schema"
        result["is_dict_key_or_schema"] = True
        return result

    if re.search(rf"['\"]{re.escape(term)}['\"]", stripped) and any(x in stripped for x in ["[", "]", "(", ")", "{", "}"]):
        result["expression_kind"] = "list_tuple_set_or_literal_reference"
        result["is_list_or_tuple_reference"] = True
        return result

    if re.search(rf"(os\.getenv|os\.environ\.get|environ\.get)\s*\(\s*['\"]{re.escape(term)}['\"]", stripped):
        result["expression_kind"] = "environment_lookup"
        result["is_env_lookup"] = True
        return result

    assignment = re.search(rf"(?i)\b{re.escape(term)}\b\s*[:=]\s*(.+)$", stripped)
    if assignment:
        value = assignment.group(1)
        result["expression_kind"] = "assignment"
        result["value_shape"] = redacted_value_shape(value)
        result["is_env_lookup"] = result["value_shape"]["looks_env_ref"]
        result["is_test_or_placeholder"] = result["value_shape"]["looks_placeholder"]
        return result

    result["expression_kind"] = "term_reference"
    return result


def decide_item(item: dict) -> dict:
    raw_path = item.get("path") or ""
    line_no = int(item.get("line_no") or 0)
    term = item.get("term") or ""
    risk = item.get("risk") or "REVIEW"

    path = ROOT / raw_path
    line = get_line(path, line_no) if path.exists() else ""
    shape = classify_expression_shape(line, term)

    low_path = raw_path.lower()

    if low_path.startswith("docs/") or low_path.endswith(".md") or low_path.endswith(".txt"):
        decision = "DOC_REFERENCE"
        action = "Dokümantasyon referansı; secret değeri yazılmadığı sürece rotate gerektirmez."
        normalized_risk = "LOW"
    elif ".example" in low_path or "example" in low_path or "sample" in low_path or "template" in low_path:
        decision = "EXAMPLE_OR_TEMPLATE"
        action = "Örnek/şablon dosyası; gerçek değer yoksa rotate gerektirmez."
        normalized_risk = "LOW"
    elif low_path.startswith("tests/"):
        decision = "TEST_REFERENCE"
        action = "Test fixture veya test fallback olabilir; canlı secret kabul edilmez, ayrı doğrulanmalı."
        normalized_risk = "REVIEW"
    elif low_path.startswith("scripts/quality/") or low_path.startswith("scripts/security/") or low_path.startswith("scripts/maintenance/"):
        decision = "AUDIT_OR_TOOLING_REFERENCE"
        action = "Audit/onarım script referansı olabilir; gerçek değer gömülü değilse rotate gerektirmez."
        normalized_risk = "REVIEW"
    elif shape["is_dict_key_or_schema"] or shape["is_list_or_tuple_reference"]:
        decision = "SCHEMA_OR_GUARDRAIL_REFERENCE"
        action = "Güvenlik kontrol listesi veya schema anahtarı olabilir; secret değeri gibi değerlendirilmemeli."
        normalized_risk = "LOW"
    elif shape["is_env_lookup"]:
        decision = "ENV_LOOKUP_REFERENCE"
        action = "Ortam değişkeni okuma; değer kodda değilse rotate gerektirmez."
        normalized_risk = "LOW"
    elif shape["expression_kind"] == "assignment" and shape["value_shape"]["looks_placeholder"]:
        decision = "PLACEHOLDER_ASSIGNMENT"
        action = "Placeholder/test değeri gibi görünüyor; canlı konfigürasyonda kullanılmadığı doğrulanmalı."
        normalized_risk = "REVIEW"
    elif shape["expression_kind"] == "assignment" and shape["value_shape"]["looks_secretish"]:
        decision = "POSSIBLE_HARDCODED_SECRET"
        action = "Gerçek değer olma ihtimali var. Değer gösterilmeden manuel doğrulama ve gerekiyorsa rotate yapılmalı."
        normalized_risk = "HIGH"
    elif shape["expression_kind"] == "assignment" and risk == "HIGH":
        decision = "POSSIBLE_HARDCODED_CONFIG_VALUE"
        action = "Sabit değer atanmış olabilir. Canlı secret mı, test/dev fallback mi manuel doğrulanmalı."
        normalized_risk = "HIGH" if raw_path in {"config.py"} or low_path.startswith("app/") else "REVIEW"
    else:
        decision = "REFERENCE_REVIEW"
        action = "Terim referansı; değer yoksa düşük risk, ancak dosya bağlamı incelenmeli."
        normalized_risk = "REVIEW"

    return {
        "path": raw_path,
        "line_no": line_no,
        "term": term,
        "original_risk": risk,
        "normalized_risk": normalized_risk,
        "decision": decision,
        "action": action,
        "expression_kind": shape["expression_kind"],
        "value_shape": shape["value_shape"],
        "note": "Satır/değer rapora yazılmadı; yalnızca karar ve şekil bilgisi tutuldu.",
    }


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)

    s0b = read_json(S0B_JSON)

    source_findings = []
    source_findings.extend(s0b.get("high_risk_findings_top_200", []))
    source_findings.extend(s0b.get("review_findings_top_200", []))

    seen = set()
    unique = []
    for item in source_findings:
        key = (item.get("path"), item.get("line_no"), item.get("term"))
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    decisions = [decide_item(item) for item in unique]

    by_decision = Counter(item["decision"] for item in decisions)
    by_risk = Counter(item["normalized_risk"] for item in decisions)
    by_term = Counter(item["term"] for item in decisions)
    by_path = Counter(item["path"] for item in decisions)

    high = [item for item in decisions if item["normalized_risk"] == "HIGH"]
    review = [item for item in decisions if item["normalized_risk"] == "REVIEW"]

    rotate_terms = sorted({item["term"] for item in high})
    rotate_paths = sorted({item["path"] for item in high})

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    compile_result = run_cmd([
        str(py),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
    ])

    pytest_result = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests/quality",
        "-m",
        "ci_safe",
        "-q",
        "-ra",
    ])

    pytest_summary = parse_pytest_summary(pytest_result["combined_tail"])
    ok = compile_result["returncode"] == 0 and pytest_result["returncode"] == 0

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0B2_SECRET_RISK_DECISION_MATRIX",
        "mode": "audit_only_no_code_change_no_secret_values",
        "ok": ok,
        "decision": "S0B2_HIGH_RISK_MANUAL_SECRET_REVIEW_REQUIRED" if high else "S0B2_NO_HIGH_RISK_AFTER_CLASSIFICATION",
        "source_s0b_ok": s0b.get("ok"),
        "source_s0b_high_risk_count": s0b.get("high_risk_count"),
        "source_s0b_review_risk_count": s0b.get("review_risk_count"),
        "classified_item_count": len(decisions),
        "normalized_high_count": len(high),
        "normalized_review_count": len(review),
        "by_normalized_risk": dict(by_risk),
        "by_decision": dict(by_decision),
        "by_term": dict(by_term),
        "by_path_top_80": dict(by_path.most_common(80)),
        "rotate_review_terms": rotate_terms,
        "rotate_review_paths": rotate_paths,
        "high_decisions": high[:200],
        "review_decisions": review[:200],
        "all_decisions_top_500": decisions[:500],
        "compileall_returncode": compile_result["returncode"],
        "pytest_quality_smoke_returncode": pytest_result["returncode"],
        "pytest_quality_smoke_summary": pytest_summary,
        "next_action": "HIGH varsa S0B3 manuel rotate karar raporu; HIGH yoksa S0C config.py bug fix.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 S0B2 Secret Risk Decision Matrix",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Source S0B OK: {result['source_s0b_ok']}",
        f"- Source S0B high risk count: {result['source_s0b_high_risk_count']}",
        f"- Source S0B review risk count: {result['source_s0b_review_risk_count']}",
        f"- Classified item count: {result['classified_item_count']}",
        f"- Normalized high count: {result['normalized_high_count']}",
        f"- Normalized review count: {result['normalized_review_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        "",
        "## Pytest Quality Smoke Summary",
        "",
        "```json",
        json.dumps(pytest_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## By Normalized Risk",
        "",
        "```json",
        json.dumps(result["by_normalized_risk"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## By Decision",
        "",
        "```json",
        json.dumps(result["by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Rotate Review Terms",
        "",
        "```json",
        json.dumps(rotate_terms, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Rotate Review Paths",
        "",
        "```json",
        json.dumps(rotate_paths, ensure_ascii=False, indent=2),
        "```",
        "",
        "## High Decisions",
        "",
        "```json",
        json.dumps(result["high_decisions"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Review Decisions",
        "",
        "```json",
        json.dumps(result["review_decisions"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("S0B2_REPORT_JSON:", OUT_JSON)
    print("S0B2_REPORT_MD:", OUT_MD)
    print("S0B2_DECISION:", result["decision"])
    print("S0B2_CLASSIFIED_ITEM_COUNT:", result["classified_item_count"])
    print("S0B2_NORMALIZED_HIGH_COUNT:", result["normalized_high_count"])
    print("S0B2_NORMALIZED_REVIEW_COUNT:", result["normalized_review_count"])
    print("S0B2_BY_NORMALIZED_RISK:", json.dumps(result["by_normalized_risk"], ensure_ascii=False))
    print("S0B2_BY_DECISION:", json.dumps(result["by_decision"], ensure_ascii=False))
    print("S0B2_ROTATE_REVIEW_TERMS:", json.dumps(result["rotate_review_terms"], ensure_ascii=False))
    print("S0B2_ROTATE_REVIEW_PATHS:", json.dumps(result["rotate_review_paths"], ensure_ascii=False))
    print("S0B2_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0B2_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0B2_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
