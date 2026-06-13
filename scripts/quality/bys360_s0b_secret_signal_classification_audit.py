from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"

S0A_JSON = QUALITY / "BYS360_S0A_CLAUDE_FINDINGS_VERIFICATION_AUDIT.json"

OUT_JSON = QUALITY / "BYS360_S0B_SECRET_SIGNAL_CLASSIFICATION_AUDIT.json"
OUT_MD = QUALITY / "BYS360_S0B_SECRET_SIGNAL_CLASSIFICATION_AUDIT.md"

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

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "reports",
    "logs",
    "releases",
    "archive",
    "backups",
}

TEXT_SUFFIXES = {
    ".py",
    ".txt",
    ".md",
    ".env",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".ps1",
    ".bat",
    ".cmd",
    ".sh",
    ".example",
    ".template",
}


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


def should_scan(path: Path) -> bool:
    if not path.is_file():
        return False

    if set(path.parts) & EXCLUDE_DIRS:
        return False

    if path.name.lower().startswith(".env"):
        return True

    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return True

    if path.name.lower() in {"dockerfile", "makefile"}:
        return True

    return False


def redacted_shape(value: str) -> dict:
    raw = value.strip().strip('"').strip("'")
    if not raw:
        return {
            "has_value": False,
            "length_bucket": "empty",
            "looks_placeholder": True,
            "looks_url": False,
            "looks_secretish": False,
        }

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
    ]

    looks_placeholder = any(x in low for x in placeholders)

    length = len(raw)
    if length <= 8:
        bucket = "1-8"
    elif length <= 20:
        bucket = "9-20"
    elif length <= 40:
        bucket = "21-40"
    elif length <= 80:
        bucket = "41-80"
    else:
        bucket = "80+"

    looks_url = bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw))
    has_mixed = bool(re.search(r"[A-Z]", raw)) and bool(re.search(r"[a-z]", raw))
    has_digit = bool(re.search(r"\d", raw))
    has_symbol = bool(re.search(r"[^A-Za-z0-9_:/@.\-]", raw))
    looks_secretish = length >= 24 and (has_mixed or has_digit or has_symbol) and not looks_placeholder

    return {
        "has_value": True,
        "length_bucket": bucket,
        "looks_placeholder": looks_placeholder,
        "looks_url": looks_url,
        "looks_secretish": looks_secretish,
    }


def classify_line(path: Path, line: str, term: str) -> dict:
    stripped = line.strip()
    low_path = str(path).lower()
    low_line = stripped.lower()

    is_doc = path.suffix.lower() in {".md", ".txt"} or "/docs/" in low_path or "\\docs\\" in low_path
    is_example = any(x in low_path for x in [".example", "example", "sample", "template"])
    is_env_file = path.name.lower().startswith(".env")
    is_config_like = path.suffix.lower() in {".env", ".ini", ".toml", ".yml", ".yaml", ".json"}

    assignment_match = re.search(
        rf"(?i)\b{re.escape(term)}\b\s*[:=]\s*(.+)$",
        stripped,
    )

    os_getenv_match = re.search(
        rf"(?i)(os\.getenv|os\.environ\.get|environ\.get)\s*\(\s*['\"]{re.escape(term)}['\"]",
        stripped,
    )

    if os_getenv_match:
        category = "code_env_reference"
        risk = "LOW"
        value_shape = redacted_shape("")
    elif is_doc:
        category = "documentation_reference"
        risk = "LOW"
        value_shape = redacted_shape("")
    elif assignment_match:
        value_shape = redacted_shape(assignment_match.group(1))

        if is_example or value_shape["looks_placeholder"]:
            category = "placeholder_or_example_assignment"
            risk = "LOW"
        elif is_env_file or is_config_like:
            category = "active_config_assignment"
            risk = "HIGH" if value_shape["looks_secretish"] or value_shape["has_value"] else "REVIEW"
        else:
            category = "code_or_script_assignment"
            risk = "HIGH" if value_shape["looks_secretish"] or value_shape["has_value"] else "REVIEW"
    else:
        value_shape = redacted_shape("")
        category = "term_reference"
        risk = "REVIEW" if not is_doc else "LOW"

    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "line_no": None,
        "term": term,
        "category": category,
        "risk": risk,
        "is_env_file": is_env_file,
        "is_doc": is_doc,
        "is_example": is_example,
        "value_shape": value_shape,
        "note": "Değer yazılmadı; sadece şekil/sınıf bilgisi üretildi.",
    }


def scan_secret_signals() -> list[dict]:
    findings = []

    for path in ROOT.rglob("*"):
        if not should_scan(path):
            continue

        text = read_text_safe(path)
        if not text:
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            for term in SECRET_TERMS:
                if term not in line:
                    continue

                item = classify_line(path, line, term)
                item["line_no"] = line_no
                findings.append(item)

    return findings


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)

    s0a = read_json(S0A_JSON)
    findings = scan_secret_signals()

    by_risk = Counter(item["risk"] for item in findings)
    by_category = Counter(item["category"] for item in findings)
    by_term = Counter(item["term"] for item in findings)
    by_path = Counter(item["path"] for item in findings)

    high_findings = [item for item in findings if item["risk"] == "HIGH"]
    review_findings = [item for item in findings if item["risk"] == "REVIEW"]

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
        "phase": "S0B_SECRET_SIGNAL_CLASSIFICATION_AUDIT",
        "mode": "audit_only_no_code_change_no_secret_values",
        "ok": ok,
        "decision": "S0B_SECRET_REVIEW_REQUIRED" if high_findings or review_findings else "S0B_NO_ACTIVE_SECRET_SIGNAL",
        "source_s0a_ok": s0a.get("ok"),
        "source_s0a_worktree_secret_term_hit_count": (
            s0a.get("checks", {})
            .get("worktree_secret_terms", {})
            .get("worktree_secret_term_hit_count")
        ),
        "secret_signal_count": len(findings),
        "high_risk_count": len(high_findings),
        "review_risk_count": len(review_findings),
        "by_risk": dict(by_risk),
        "by_category": dict(by_category),
        "by_term": dict(by_term),
        "by_path_top_80": dict(by_path.most_common(80)),
        "high_risk_findings_top_200": high_findings[:200],
        "review_findings_top_200": review_findings[:200],
        "all_findings_top_500": findings[:500],
        "compileall_returncode": compile_result["returncode"],
        "pytest_quality_smoke_returncode": pytest_result["returncode"],
        "pytest_quality_smoke_summary": pytest_summary,
        "next_action": "HIGH varsa S0B2: değer göstermeden dosya bazlı secret risk kararı ve rotate listesi hazırlanmalı; HIGH yoksa S0C config.py bug fix yapılmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 S0B Secret Signal Classification Audit",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Source S0A OK: {result['source_s0a_ok']}",
        f"- Source S0A worktree secret term hit count: {result['source_s0a_worktree_secret_term_hit_count']}",
        f"- Secret signal count: {result['secret_signal_count']}",
        f"- High risk count: {result['high_risk_count']}",
        f"- Review risk count: {result['review_risk_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        "",
        "## Pytest Quality Smoke Summary",
        "",
        "```json",
        json.dumps(pytest_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## By Risk",
        "",
        "```json",
        json.dumps(result["by_risk"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## By Category",
        "",
        "```json",
        json.dumps(result["by_category"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## By Term",
        "",
        "```json",
        json.dumps(result["by_term"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## By Path Top 80",
        "",
        "```json",
        json.dumps(result["by_path_top_80"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## High Risk Findings Top 200",
        "",
        "```json",
        json.dumps(result["high_risk_findings_top_200"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Review Findings Top 200",
        "",
        "```json",
        json.dumps(result["review_findings_top_200"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("S0B_REPORT_JSON:", OUT_JSON)
    print("S0B_REPORT_MD:", OUT_MD)
    print("S0B_DECISION:", result["decision"])
    print("S0B_SECRET_SIGNAL_COUNT:", result["secret_signal_count"])
    print("S0B_HIGH_RISK_COUNT:", result["high_risk_count"])
    print("S0B_REVIEW_RISK_COUNT:", result["review_risk_count"])
    print("S0B_BY_RISK:", json.dumps(result["by_risk"], ensure_ascii=False))
    print("S0B_BY_CATEGORY:", json.dumps(result["by_category"], ensure_ascii=False))
    print("S0B_BY_TERM:", json.dumps(result["by_term"], ensure_ascii=False))
    print("S0B_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0B_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0B_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
