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
BACKUP_ROOT = RELEASES / f"S0C3_REMAINING_SECRETKEY_BLOCK_HOTFIX_BACKUP_{STAMP}"

OUT_JSON = QUALITY / "BYS360_S0C3_REMAINING_SECRETKEY_BLOCK_HOTFIX.json"
OUT_MD = QUALITY / "BYS360_S0C3_REMAINING_SECRETKEY_BLOCK_HOTFIX.md"

S0C2_SCRIPT = ROOT / "scripts" / "quality" / "bys360_s0c2_config_secretkey_exc_final_evidence.py"
S0C2_JSON = QUALITY / "BYS360_S0C2_CONFIG_SECRETKEY_EXC_FINAL_EVIDENCE.json"


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


def block_has_env_secret(block: str) -> bool:
    return (
        'os.environ.get("SECRET_KEY")' in block
        or "os.getenv(\"SECRET_KEY\")" in block
        or "os.getenv('SECRET_KEY')" in block
        or "environ.get(\"SECRET_KEY\")" in block
        or "environ.get('SECRET_KEY')" in block
        or 'os.environ.get("FLASK_SECRET")' in block
        or "os.getenv(\"FLASK_SECRET\")" in block
        or "os.getenv('FLASK_SECRET')" in block
        or "environ.get(\"FLASK_SECRET\")" in block
        or "environ.get('FLASK_SECRET')" in block
    )


def find_secret_key_blocks(lines: list[str]) -> list[dict]:
    blocks = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if not re.match(r"^(\s*)SECRET_KEY\s*=", line):
            i += 1
            continue

        start = i
        balance = 0
        started = False
        end = i

        for j in range(i, min(len(lines), i + 30)):
            current = lines[j]

            for ch in current:
                if ch in "([{":
                    balance += 1
                    started = True
                elif ch in ")]}":
                    balance -= 1

            end = j

            if j == start and not started:
                break

            if started and balance <= 0:
                break

        block = "\n".join(lines[start:end + 1])
        blocks.append({
            "start": start,
            "end": end,
            "line_no": start + 1,
            "indent": re.match(r"^(\s*)", lines[start]).group(1),
            "has_env_secret": block_has_env_secret(block),
        })

        i = end + 1

    return blocks


def replacement_block(indent: str) -> list[str]:
    return [
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


def patch_remaining_secret_key_blocks(lines: list[str]) -> tuple[list[str], list[dict]]:
    blocks = find_secret_key_blocks(lines)
    operations = []

    new_lines = list(lines)

    for block in reversed(blocks):
        if block["has_env_secret"]:
            continue

        repl = replacement_block(block["indent"])
        new_lines[block["start"]:block["end"] + 1] = repl

        operations.append({
            "type": "remaining_secret_key_block_env_centered",
            "line_no": block["line_no"],
            "status": "patched",
            "note": "Env merkezli olmayan SECRET_KEY bloğu ortam değişkeni merkezli hale getirildi; değer rapora yazılmadı.",
        })

    operations.reverse()
    return new_lines, operations


def scan_secret_key_blocks_after() -> dict:
    text = TARGET.read_text(encoding="utf-8-sig", errors="ignore")
    lines = text.splitlines()
    blocks = find_secret_key_blocks(lines)

    safe = []
    high = []

    for block in blocks:
        row = {
            "line_no": block["line_no"],
            "has_env_secret": block["has_env_secret"],
            "normalized_risk": "LOW" if block["has_env_secret"] else "HIGH",
            "note": "Blok içeriği/değer rapora yazılmadı.",
        }
        if block["has_env_secret"]:
            safe.append(row)
        else:
            high.append(row)

    return {
        "secret_key_block_count": len(blocks),
        "secret_key_high_risk_count": len(high),
        "secret_key_safe_block_count": len(safe),
        "blocks": safe + high,
    }


def scan_exc_after() -> dict:
    text = TARGET.read_text(encoding="utf-8-sig", errors="ignore")
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
        "exc_bug_likely_after_patch": any(item["bug_likely"] for item in findings),
        "findings": findings,
    }


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)

    if not TARGET.exists():
        print("S0C3_OK:", False)
        print("S0C3_DECISION: S0C3_BLOCKED_CONFIG_NOT_FOUND")
        return 1

    backup_path = BACKUP_ROOT / "config.py"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, backup_path)

    original = TARGET.read_text(encoding="utf-8-sig", errors="ignore")
    lines = original.splitlines()

    new_lines, operations = patch_remaining_secret_key_blocks(lines)
    updated = "\n".join(new_lines) + ("\n" if original.endswith("\n") else "")

    file_changed = updated != original

    if file_changed:
        TARGET.write_text(updated, encoding="utf-8")

    post_secret_scan = scan_secret_key_blocks_after()
    post_exc_scan = scan_exc_after()

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

    s0c2_rerun = {"returncode": None}
    if S0C2_SCRIPT.exists():
        s0c2_proc = run_cmd([str(py), str(S0C2_SCRIPT)], timeout=1800)
        s0c2_json = read_json(S0C2_JSON)
        s0c2_rerun = {
            "returncode": s0c2_proc["returncode"],
            "ok": s0c2_json.get("ok"),
            "decision": s0c2_json.get("decision"),
            "secret_key_high_risk_count": (
                s0c2_json.get("secret_key_scan", {})
                .get("secret_key_high_risk_count")
            ),
            "repo_normalized_high_count": (
                s0c2_json.get("repo_secret_scan", {})
                .get("normalized_high_count")
            ),
        }

    ok = (
        file_changed
        and bool(operations)
        and compile_result["returncode"] == 0
        and quality_smoke["returncode"] == 0
        and full_pytest["returncode"] == 0
        and full_summary.get("failed", 0) == 0
        and full_summary.get("errors", 0) == 0
        and full_summary.get("warnings", 0) == 0
        and full_summary.get("passed", 0) >= 700
        and post_secret_scan["secret_key_high_risk_count"] == 0
        and post_exc_scan["exc_bug_likely_after_patch"] is False
        and s0c2_rerun.get("secret_key_high_risk_count") == 0
        and s0c2_rerun.get("repo_normalized_high_count") == 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0C3_REMAINING_SECRETKEY_BLOCK_HOTFIX",
        "mode": "safe_code_change_with_backup_no_secret_values",
        "ok": ok,
        "decision": "S0C3_GREEN" if ok else "S0C3_REVIEW_REQUIRED",
        "target": "config.py",
        "backup_path": str(backup_path),
        "file_changed": file_changed,
        "operation_count": len(operations),
        "operations": operations,
        "post_secret_scan": post_secret_scan,
        "post_exc_scan": post_exc_scan,
        "compileall_returncode": compile_result["returncode"],
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": quality_summary,
        "pytest_full_returncode": full_pytest["returncode"],
        "pytest_full_summary": full_summary,
        "s0c2_rerun": s0c2_rerun,
        "next_action": "S0D pytest config çatışması ve backup test collection düzeltmesine geçilebilir." if ok else "S0C3 raporu incelenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 S0C3 Remaining SECRET_KEY Block Hotfix",
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
        f"- SECRET_KEY high risk count: {post_secret_scan['secret_key_high_risk_count']}",
        f"- Exc bug likely after patch: {post_exc_scan['exc_bug_likely_after_patch']}",
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
        "## Post SECRET_KEY Scan",
        "",
        "```json",
        json.dumps(post_secret_scan, ensure_ascii=False, indent=2),
        "```",
        "",
        "## S0C2 Rerun",
        "",
        "```json",
        json.dumps(s0c2_rerun, ensure_ascii=False, indent=2),
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

    print("S0C3_REPORT_JSON:", OUT_JSON)
    print("S0C3_REPORT_MD:", OUT_MD)
    print("S0C3_BACKUP_PATH:", backup_path)
    print("S0C3_FILE_CHANGED:", result["file_changed"])
    print("S0C3_OPERATION_COUNT:", result["operation_count"])
    print("S0C3_SECRET_KEY_HIGH_RISK_COUNT:", post_secret_scan["secret_key_high_risk_count"])
    print("S0C3_EXC_BUG_LIKELY_AFTER_PATCH:", post_exc_scan["exc_bug_likely_after_patch"])
    print("S0C3_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0C3_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0C3_PYTEST_FULL_RETURN_CODE:", result["pytest_full_returncode"])
    print("S0C3_PYTEST_FULL_SUMMARY:", json.dumps(full_summary, ensure_ascii=False))
    print("S0C3_S0C2_OK:", s0c2_rerun.get("ok"))
    print("S0C3_S0C2_SECRET_KEY_HIGH_RISK_COUNT:", s0c2_rerun.get("secret_key_high_risk_count"))
    print("S0C3_S0C2_REPO_NORMALIZED_HIGH_COUNT:", s0c2_rerun.get("repo_normalized_high_count"))
    print("S0C3_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
