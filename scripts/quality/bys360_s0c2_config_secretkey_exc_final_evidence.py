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

OUT_JSON = QUALITY / "BYS360_S0C2_CONFIG_SECRETKEY_EXC_FINAL_EVIDENCE.json"
OUT_MD = QUALITY / "BYS360_S0C2_CONFIG_SECRETKEY_EXC_FINAL_EVIDENCE.md"

TARGET = ROOT / "config.py"

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


def run_cmd(cmd, timeout=1800):
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="ignore",
            env={
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
                "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
            },
            timeout=timeout,
        )
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": proc.returncode,
            "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-20000:],
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="ignore")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="ignore")
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 124,
            "combined_tail": (stdout + "\n" + stderr + "\nTIMEOUT")[-20000:],
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


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""


def get_assignment_block(lines: list[str], start_index: int) -> str:
    block = []
    balance = 0
    started = False

    for idx in range(start_index, min(len(lines), start_index + 20)):
        line = lines[idx]
        block.append(line)

        for ch in line:
            if ch in "([{":
                balance += 1
                started = True
            elif ch in ")]}":
                balance -= 1

        stripped = line.strip()

        if idx == start_index and not started:
            break

        if started and balance <= 0:
            break

        if idx > start_index and not stripped.endswith((",", "or", "and", "\\", "(")):
            if balance <= 0:
                break

    return "\n".join(block)


def classify_secret_key_blocks() -> dict:
    text = read_text(TARGET)
    lines = text.splitlines()

    blocks = []

    for idx, line in enumerate(lines):
        if not re.match(r"^\s*SECRET_KEY\s*=", line):
            continue

        block = get_assignment_block(lines, idx)

        has_env_secret = (
            'os.environ.get("SECRET_KEY")' in block
            or "os.getenv(\"SECRET_KEY\")" in block
            or "os.getenv('SECRET_KEY')" in block
            or "environ.get(\"SECRET_KEY\")" in block
            or "environ.get('SECRET_KEY')" in block
        )

        has_env_flask_secret = (
            'os.environ.get("FLASK_SECRET")' in block
            or "os.getenv(\"FLASK_SECRET\")" in block
            or "os.getenv('FLASK_SECRET')" in block
            or "environ.get(\"FLASK_SECRET\")" in block
            or "environ.get('FLASK_SECRET')" in block
        )

        has_prod_guard = (
            "production" in block.lower()
            or "prod" in block.lower()
            or "live" in block.lower()
        )

        has_local_dev_fallback = "local-dev" in block.lower() or "dev-only" in block.lower()

        block_is_env_centered = has_env_secret or has_env_flask_secret

        high_risk = not block_is_env_centered

        if block_is_env_centered and has_local_dev_fallback and has_prod_guard:
            decision = "ENV_CENTERED_WITH_LOCAL_DEV_ONLY_FALLBACK"
            normalized_risk = "LOW"
        elif block_is_env_centered:
            decision = "ENV_CENTERED_SECRET_KEY"
            normalized_risk = "LOW"
        else:
            decision = "POSSIBLE_HARDCODED_SECRET_KEY"
            normalized_risk = "HIGH"

        blocks.append({
            "line_no": idx + 1,
            "decision": decision,
            "normalized_risk": normalized_risk,
            "has_env_secret": has_env_secret,
            "has_env_flask_secret": has_env_flask_secret,
            "has_prod_guard": has_prod_guard,
            "has_local_dev_fallback": has_local_dev_fallback,
            "note": "Blok içeriği/değer rapora yazılmadı; yalnızca güvenli şekil bilgisi tutuldu.",
        })

    return {
        "secret_key_block_count": len(blocks),
        "secret_key_high_risk_count": sum(1 for item in blocks if item["normalized_risk"] == "HIGH"),
        "secret_key_blocks": blocks,
    }


def scan_exc_bug_after_patch() -> dict:
    text = read_text(TARGET)
    lines = text.splitlines()

    findings = []

    for idx, line in enumerate(lines, start=1):
        if "exc_info=exc" not in line:
            continue

        window = "\n".join(lines[max(0, idx - 12):idx])
        plain_except = bool(re.search(r"except\s+Exception\s*:", window))
        as_exc = bool(re.search(r"except\s+Exception\s+as\s+exc\s*:", window))

        findings.append({
            "line_no": idx,
            "plain_except_nearby": plain_except,
            "except_exception_as_exc_nearby": as_exc,
            "bug_likely": plain_except and not as_exc,
        })

    return {
        "exc_info_exc_line_count": len(findings),
        "exc_bug_likely_after_patch": any(item["bug_likely"] for item in findings),
        "findings": findings,
    }


def should_scan_file(path: Path) -> bool:
    if not path.is_file():
        return False

    low_parts = [part.lower() for part in path.parts]

    for part in low_parts:
        if part in {".git", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", "reports", "logs", "releases", "archive", "backups"}:
            return False
        if part.startswith(".venv") or part.startswith("venv_old") or "backup" in part:
            return False

    if path.name.lower().startswith(".env"):
        return True

    return path.suffix.lower() in {
        ".py", ".txt", ".md", ".env", ".json", ".yml", ".yaml",
        ".toml", ".ini", ".ps1", ".bat", ".cmd", ".sh"
    }


def classify_repo_secret_terms_after_s0c() -> dict:
    findings = []

    for path in ROOT.rglob("*"):
        if not should_scan_file(path):
            continue

        text = read_text(path)
        if not text:
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            for term in SECRET_TERMS:
                if term not in line:
                    continue

                low_path = str(path.relative_to(ROOT)).replace("\\", "/").lower()
                stripped = line.strip()

                is_doc = low_path.startswith("docs/") or low_path.endswith(".md") or low_path.endswith(".txt")
                is_test = low_path.startswith("tests/")
                is_example = "example" in low_path or "template" in low_path or "sample" in low_path
                is_tooling = low_path.startswith("scripts/quality/") or low_path.startswith("scripts/security/") or low_path.startswith("scripts/maintenance/")
                is_env_lookup = bool(re.search(rf"(os\.getenv|os\.environ\.get|environ\.get)\s*\(\s*['\"]{re.escape(term)}['\"]", stripped))
                is_schema_key = bool(re.search(rf"['\"]{re.escape(term)}['\"]\s*:", stripped))
                is_literal_ref = bool(re.search(rf"['\"]{re.escape(term)}['\"]", stripped))

                if is_doc:
                    decision = "DOC_REFERENCE"
                    risk = "LOW"
                elif is_example:
                    decision = "EXAMPLE_OR_TEMPLATE"
                    risk = "LOW"
                elif is_env_lookup:
                    decision = "ENV_LOOKUP_REFERENCE"
                    risk = "LOW"
                elif is_schema_key or is_literal_ref:
                    decision = "SCHEMA_OR_GUARDRAIL_REFERENCE"
                    risk = "LOW"
                elif is_test:
                    decision = "TEST_REFERENCE"
                    risk = "REVIEW"
                elif is_tooling:
                    decision = "AUDIT_OR_TOOLING_REFERENCE"
                    risk = "REVIEW"
                elif low_path == "config.py" and term == "SECRET_KEY":
                    continue
                else:
                    decision = "REFERENCE_REVIEW"
                    risk = "REVIEW"

                findings.append({
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "line_no": line_no,
                    "term": term,
                    "decision": decision,
                    "normalized_risk": risk,
                    "note": "Satır/değer rapora yazılmadı.",
                })

    by_risk = Counter(item["normalized_risk"] for item in findings)
    by_decision = Counter(item["decision"] for item in findings)
    by_term = Counter(item["term"] for item in findings)
    by_path = Counter(item["path"] for item in findings)

    return {
        "classified_signal_count": len(findings),
        "normalized_high_count": by_risk.get("HIGH", 0),
        "normalized_review_count": by_risk.get("REVIEW", 0),
        "by_risk": dict(by_risk),
        "by_decision": dict(by_decision),
        "by_term": dict(by_term),
        "by_path_top_80": dict(by_path.most_common(80)),
        "review_findings_top_200": [item for item in findings if item["normalized_risk"] == "REVIEW"][:200],
    }


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)

    exc_scan = scan_exc_bug_after_patch()
    secret_key_scan = classify_secret_key_blocks()
    repo_secret_scan = classify_repo_secret_terms_after_s0c()

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    compile_result = run_cmd([
        str(py),
        "-m",
        "compileall",
        "-q",
        "config.py",
        "app",
        "scripts",
        "migrations",
    ])

    quality_smoke = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests/quality",
        "-m",
        "ci_safe",
        "-q",
        "-ra",
    ])

    full_pytest = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ])

    quality_summary = parse_pytest_summary(quality_smoke["combined_tail"])
    full_summary = parse_pytest_summary(full_pytest["combined_tail"])

    ok = (
        compile_result["returncode"] == 0
        and quality_smoke["returncode"] == 0
        and full_pytest["returncode"] == 0
        and full_summary.get("failed", 0) == 0
        and full_summary.get("errors", 0) == 0
        and full_summary.get("warnings", 0) == 0
        and full_summary.get("passed", 0) >= 700
        and exc_scan["exc_bug_likely_after_patch"] is False
        and secret_key_scan["secret_key_high_risk_count"] == 0
        and repo_secret_scan["normalized_high_count"] == 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0C2_CONFIG_SECRETKEY_EXC_FINAL_EVIDENCE",
        "mode": "evidence_only_no_code_change_no_secret_values",
        "ok": ok,
        "decision": "S0C2_GREEN" if ok else "S0C2_REVIEW_REQUIRED",
        "exc_scan": exc_scan,
        "secret_key_scan": secret_key_scan,
        "repo_secret_scan": repo_secret_scan,
        "compileall_returncode": compile_result["returncode"],
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": quality_summary,
        "pytest_full_returncode": full_pytest["returncode"],
        "pytest_full_summary": full_summary,
        "next_action": "S0D pytest config çatışması ve backup test collection düzeltmesine geçilebilir." if ok else "S0C2 raporu incelenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 S0C2 config.py SECRET_KEY ve exc Final Evidence",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        f"- Pytest full returncode: {result['pytest_full_returncode']}",
        f"- Exc bug likely after patch: {exc_scan['exc_bug_likely_after_patch']}",
        f"- SECRET_KEY high risk count: {secret_key_scan['secret_key_high_risk_count']}",
        f"- Repo normalized high count: {repo_secret_scan['normalized_high_count']}",
        "",
        "## Exc Scan",
        "",
        "```json",
        json.dumps(exc_scan, ensure_ascii=False, indent=2),
        "```",
        "",
        "## SECRET_KEY Scan",
        "",
        "```json",
        json.dumps(secret_key_scan, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Repo Secret Scan",
        "",
        "```json",
        json.dumps(repo_secret_scan, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Quality Smoke Summary",
        "",
        "```json",
        json.dumps(quality_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Full Summary",
        "",
        "```json",
        json.dumps(full_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("S0C2_REPORT_JSON:", OUT_JSON)
    print("S0C2_REPORT_MD:", OUT_MD)
    print("S0C2_EXC_BUG_LIKELY_AFTER_PATCH:", exc_scan["exc_bug_likely_after_patch"])
    print("S0C2_SECRET_KEY_HIGH_RISK_COUNT:", secret_key_scan["secret_key_high_risk_count"])
    print("S0C2_REPO_NORMALIZED_HIGH_COUNT:", repo_secret_scan["normalized_high_count"])
    print("S0C2_REPO_NORMALIZED_REVIEW_COUNT:", repo_secret_scan["normalized_review_count"])
    print("S0C2_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0C2_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0C2_PYTEST_FULL_RETURN_CODE:", result["pytest_full_returncode"])
    print("S0C2_PYTEST_FULL_SUMMARY:", json.dumps(full_summary, ensure_ascii=False))
    print("S0C2_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
