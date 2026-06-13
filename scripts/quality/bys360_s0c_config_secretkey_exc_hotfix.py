from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import os
import re
import shutil
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

TARGET = ROOT / "config.py"
BACKUP_ROOT = RELEASES / f"S0C_CONFIG_SECRETKEY_EXC_HOTFIX_BACKUP_{STAMP}"

OUT_JSON = QUALITY / "BYS360_S0C_CONFIG_SECRETKEY_EXC_HOTFIX.json"
OUT_MD = QUALITY / "BYS360_S0C_CONFIG_SECRETKEY_EXC_HOTFIX.md"

S0B2_SCRIPT = ROOT / "scripts" / "quality" / "bys360_s0b2_secret_risk_decision_matrix.py"
S0B2_JSON = QUALITY / "BYS360_S0B2_SECRET_RISK_DECISION_MATRIX.json"


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


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc)}


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


def ensure_import_os(lines: list[str]) -> tuple[list[str], bool]:
    if any(re.match(r"\s*import\s+os\b", line) for line in lines):
        return lines, False

    insert_at = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("from __future__"):
            insert_at = i + 1

    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1

    lines.insert(insert_at, "import os")
    return lines, True


def patch_exc_bug(lines: list[str]) -> tuple[list[str], list[dict]]:
    operations = []

    for idx, line in enumerate(lines):
        if "exc_info=exc" not in line:
            continue

        start = max(0, idx - 12)
        for j in range(idx - 1, start - 1, -1):
            if re.match(r"^(\s*)except\s+Exception\s*:\s*$", lines[j]):
                old = lines[j]
                indent = re.match(r"^(\s*)", old).group(1)
                lines[j] = f"{indent}except Exception as exc:"
                operations.append({
                    "type": "config_exc_bug_fix",
                    "line_no": j + 1,
                    "status": "patched",
                    "note": "except Exception -> except Exception as exc",
                })
                return lines, operations

    return lines, operations


def patch_secret_key(lines: list[str]) -> tuple[list[str], list[dict]]:
    operations = []

    patched_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if (
            re.match(r"^(\s*)SECRET_KEY\s*=", line)
            and "os.getenv" not in line
            and "os.environ" not in line
            and "environ.get" not in line
        ):
            indent = re.match(r"^(\s*)", line).group(1)

            replacement = [
                f'{indent}SECRET_KEY = (',
                f'{indent}    os.environ.get("SECRET_KEY")',
                f'{indent}    or os.environ.get("FLASK_SECRET")',
                f'{indent}    or (',
                f'{indent}        "bys360-local-dev-only-secret"',
                f'{indent}        if os.environ.get("FLASK_ENV", "").lower() not in {{"production", "prod"}}',
                f'{indent}        and os.environ.get("BYS360_ENV", "").lower() not in {{"production", "prod", "live"}}',
                f'{indent}        else None',
                f'{indent}    )',
                f'{indent})',
            ]

            patched_lines.extend(replacement)
            operations.append({
                "type": "secret_key_env_centered_fallback",
                "line_no": i + 1,
                "status": "patched",
                "note": "SECRET_KEY sabit değer yerine ortam değişkeni merkezli hale getirildi; değer rapora yazılmadı.",
            })
            i += 1
            continue

        patched_lines.append(line)
        i += 1

    return patched_lines, operations


def scan_config_after_patch() -> dict:
    text = TARGET.read_text(encoding="utf-8-sig", errors="ignore")
    lines = text.splitlines()

    exc_bug_findings = []
    secret_key_assignment_findings = []

    for idx, line in enumerate(lines, start=1):
        if "exc_info=exc" in line:
            window = "\n".join(lines[max(0, idx - 12):idx])
            plain_except_nearby = bool(re.search(r"except\s+Exception\s*:", window))
            as_exc_nearby = bool(re.search(r"except\s+Exception\s+as\s+exc\s*:", window))
            exc_bug_findings.append({
                "line_no": idx,
                "plain_except_nearby": plain_except_nearby,
                "as_exc_nearby": as_exc_nearby,
            })

        if re.match(r"^\s*SECRET_KEY\s*=", line):
            uses_env = "os.environ" in line or "os.getenv" in line or "environ.get" in line
            secret_key_assignment_findings.append({
                "line_no": idx,
                "uses_env_on_assignment_line": uses_env,
                "note": "Satır değeri rapora yazılmadı.",
            })

    return {
        "exc_info_exc_line_count": len(exc_bug_findings),
        "exc_bug_likely_after_patch": any(
            item["plain_except_nearby"] and not item["as_exc_nearby"]
            for item in exc_bug_findings
        ),
        "exc_bug_findings": exc_bug_findings,
        "secret_key_assignment_count": len(secret_key_assignment_findings),
        "secret_key_assignment_findings": secret_key_assignment_findings,
        "secret_key_env_reference_present": (
            'os.environ.get("SECRET_KEY")' in text
            or "os.getenv(\"SECRET_KEY\")" in text
            or "os.getenv('SECRET_KEY')" in text
        ),
        "flask_secret_env_reference_present": (
            'os.environ.get("FLASK_SECRET")' in text
            or "os.getenv(\"FLASK_SECRET\")" in text
            or "os.getenv('FLASK_SECRET')" in text
        ),
    }


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)

    if not TARGET.exists():
        result = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "phase": "S0C_CONFIG_SECRETKEY_EXC_HOTFIX",
            "ok": False,
            "decision": "S0C_BLOCKED_CONFIG_NOT_FOUND",
            "target": str(TARGET),
        }
        OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("S0C_OK:", False)
        print("S0C_DECISION:", result["decision"])
        return 1

    backup_path = BACKUP_ROOT / "config.py"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, backup_path)

    original = TARGET.read_text(encoding="utf-8-sig", errors="ignore")
    lines = original.splitlines()

    lines, import_changed = ensure_import_os(lines)
    lines, exc_ops = patch_exc_bug(lines)
    lines, secret_ops = patch_secret_key(lines)

    updated = "\n".join(lines) + ("\n" if original.endswith("\n") else "")

    file_changed = updated != original

    if file_changed:
        TARGET.write_text(updated, encoding="utf-8")

    post_scan = scan_config_after_patch()

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

    full_summary = parse_pytest_summary(full_pytest["combined_tail"])
    quality_summary = parse_pytest_summary(quality_smoke["combined_tail"])

    s0b2_rerun = {"returncode": None, "summary": {}}
    if S0B2_SCRIPT.exists():
        s0b2_proc = run_cmd([str(py), str(S0B2_SCRIPT)], timeout=600)
        s0b2_latest = read_json(S0B2_JSON)
        s0b2_rerun = {
            "returncode": s0b2_proc["returncode"],
            "normalized_high_count": s0b2_latest.get("normalized_high_count"),
            "normalized_review_count": s0b2_latest.get("normalized_review_count"),
            "decision": s0b2_latest.get("decision"),
        }

    ok = (
        file_changed
        and compile_result["returncode"] == 0
        and quality_smoke["returncode"] == 0
        and full_pytest["returncode"] == 0
        and full_summary.get("failed", 0) == 0
        and full_summary.get("errors", 0) == 0
        and full_summary.get("warnings", 0) == 0
        and full_summary.get("passed", 0) >= 700
        and post_scan["exc_bug_likely_after_patch"] is False
        and post_scan["secret_key_env_reference_present"] is True
        and s0b2_rerun.get("normalized_high_count") in {0, None}
    )

    operations = []
    if import_changed:
        operations.append({
            "type": "ensure_import_os",
            "status": "patched",
        })
    operations.extend(exc_ops)
    operations.extend(secret_ops)

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0C_CONFIG_SECRETKEY_EXC_HOTFIX",
        "mode": "safe_code_change_with_backup_no_secret_values",
        "ok": ok,
        "decision": "S0C_GREEN" if ok else "S0C_REVIEW_REQUIRED",
        "target": "config.py",
        "backup_path": str(backup_path),
        "file_changed": file_changed,
        "operation_count": len(operations),
        "operations": operations,
        "post_scan": post_scan,
        "compileall_returncode": compile_result["returncode"],
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": quality_summary,
        "pytest_full_returncode": full_pytest["returncode"],
        "pytest_full_summary": full_summary,
        "s0b2_rerun": s0b2_rerun,
        "next_action": "S0D pytest config çatışması ve backup test collection düzeltmesine geçilebilir." if ok else "S0C raporu incelenmeli; gerekirse backup üzerinden geri dönüş yapılmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 S0C config.py SECRET_KEY ve exc Hotfix",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Target: {result['target']}",
        f"- Backup: `{result['backup_path']}`",
        f"- File changed: {result['file_changed']}",
        f"- Operation count: {result['operation_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        f"- Pytest full returncode: {result['pytest_full_returncode']}",
        "",
        "## Operations",
        "",
        "```json",
        json.dumps(operations, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Post Scan",
        "",
        "```json",
        json.dumps(post_scan, ensure_ascii=False, indent=2),
        "```",
        "",
        "## S0B2 Rerun",
        "",
        "```json",
        json.dumps(s0b2_rerun, ensure_ascii=False, indent=2),
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

    print("S0C_REPORT_JSON:", OUT_JSON)
    print("S0C_REPORT_MD:", OUT_MD)
    print("S0C_BACKUP_PATH:", backup_path)
    print("S0C_FILE_CHANGED:", result["file_changed"])
    print("S0C_OPERATION_COUNT:", result["operation_count"])
    print("S0C_EXC_BUG_LIKELY_AFTER_PATCH:", post_scan["exc_bug_likely_after_patch"])
    print("S0C_SECRET_KEY_ENV_REFERENCE_PRESENT:", post_scan["secret_key_env_reference_present"])
    print("S0C_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0C_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0C_PYTEST_QUALITY_SMOKE_SUMMARY:", json.dumps(quality_summary, ensure_ascii=False))
    print("S0C_PYTEST_FULL_RETURN_CODE:", result["pytest_full_returncode"])
    print("S0C_PYTEST_FULL_SUMMARY:", json.dumps(full_summary, ensure_ascii=False))
    print("S0C_S0B2_NORMALIZED_HIGH_COUNT:", s0b2_rerun.get("normalized_high_count"))
    print("S0C_S0B2_DECISION:", s0b2_rerun.get("decision"))
    print("S0C_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
