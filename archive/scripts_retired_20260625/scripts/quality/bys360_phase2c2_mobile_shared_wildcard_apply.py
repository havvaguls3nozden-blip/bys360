from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import json
import os
import re
import shutil
import subprocess

ROOT = Path(".").resolve()
ARCH = ROOT / "reports" / "architecture"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

PLAN_JSON = ARCH / "BYS360_PHASE2C1_WILDCARD_IMPORT_EXPLICIT_PLAN.json"
OUT_JSON = ARCH / "BYS360_PHASE2C2_MOBILE_SHARED_WILDCARD_IMPORT_APPLY.json"
OUT_MD = ARCH / "BYS360_PHASE2C2_MOBILE_SHARED_WILDCARD_IMPORT_APPLY.md"

BACKUP_ROOT = RELEASES / f"PHASE2C2_MOBILE_SHARED_WILDCARD_IMPORT_BACKUP_{STAMP}"
RESTORE_PS1 = BACKUP_ROOT / "RESTORE_PHASE2C2_MOBILE_SHARED_WILDCARD_IMPORT.ps1"


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
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-30000:],
        }
    except FileNotFoundError as exc:
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
            "combined_tail": str(exc)[-30000:],
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
            "stdout": stdout,
            "stderr": stderr,
            "combined_tail": (stdout + "\n" + stderr + "\nTIMEOUT")[-30000:],
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


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc)}


def get_candidates(plan: dict) -> list[dict]:
    candidates = plan.get("first_apply_candidates") or []

    safe = []
    for item in candidates:
        if (
            item.get("status") == "ready_for_explicit_import"
            and item.get("risk") == "low"
            and item.get("file", "").startswith("app/api/mobile/")
            and item.get("module") == "app.api.mobile.shared"
            and item.get("suggested_import_line")
        ):
            safe.append(item)

    return safe


def backup_file(path: Path) -> Path:
    rel = path.relative_to(ROOT)
    dst = BACKUP_ROOT / "files" / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    return dst


def write_restore_script(backups: list[dict]) -> None:
    lines = [
        '$ErrorActionPreference = "Stop"',
        'Set-Location "C:\\bys360\\project"',
        "",
    ]

    for item in backups:
        backup_path = item["backup_path"]
        rel = item["relative_path"]
        lines.extend([
            f'$src = "{backup_path}"',
            f'$dst = Join-Path "C:\\bys360\\project" "{rel}"',
            'if (Test-Path -LiteralPath $src) {',
            '  $parent = Split-Path -Parent $dst',
            '  if (!(Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }',
            '  Copy-Item -LiteralPath $src -Destination $dst -Force',
            '}',
            "",
        ])

    lines.append('Write-Host "PHASE2C2 restore tamamlandı."')
    RESTORE_PS1.parent.mkdir(parents=True, exist_ok=True)
    RESTORE_PS1.write_text("\n".join(lines), encoding="utf-8")


def replace_import_line(item: dict) -> dict:
    rel = item["file"]
    path = ROOT / rel
    line_no = int(item["line_no"])
    module = item["module"]
    suggested = item["suggested_import_line"]

    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    lines = text.splitlines(keepends=True)

    if line_no < 1 or line_no > len(lines):
        return {
            "file": rel,
            "line_no": line_no,
            "changed": False,
            "reason": "line_no_out_of_range",
        }

    old_line = lines[line_no - 1]
    stripped = old_line.strip()

    expected_pattern = rf"^\s*from\s+{re.escape(module)}\s+import\s+\*\s*(?:#.*)?$"

    if not re.match(expected_pattern, stripped):
        return {
            "file": rel,
            "line_no": line_no,
            "changed": False,
            "reason": "line_content_not_expected",
            "expected_pattern": expected_pattern,
            "actual": stripped,
        }

    newline = "\n" if old_line.endswith("\n") else ""
    indent = old_line[: len(old_line) - len(old_line.lstrip())]

    lines[line_no - 1] = indent + suggested + newline
    path.write_text("".join(lines), encoding="utf-8")

    return {
        "file": rel,
        "line_no": line_no,
        "changed": True,
        "reason": "replaced_comment_aware",
        "old_line": stripped,
        "new_line": suggested,
    }


def restore_backups(backups: list[dict]) -> None:
    for item in backups:
        src = Path(item["backup_path"])
        dst = ROOT / item["relative_path"]
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def count_mobile_shared_wildcards() -> int:
    count = 0
    for path in (ROOT / "app" / "api" / "mobile").rglob("*.py"):
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        count += len(re.findall(r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$", text, flags=re.MULTILINE))
    return count


def count_all_wildcards() -> int:
    count = 0
    for path in ROOT.rglob("*.py"):
        rel_parts = {part.lower() for part in path.relative_to(ROOT).parts}
        if rel_parts & {".git", ".venv", "venv", "reports", "releases", "__pycache__", "node_modules"}:
            continue

        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        count += len(re.findall(r"^\s*from\s+[\w\.]+\s+import\s+\*\s*(?:#.*)?$", text, flags=re.MULTILINE))

    return count


def run_validation() -> dict:
    py = ROOT / ".venv" / "Scripts" / "python.exe"

    compile_result = run_cmd([
        str(py),
        "-m",
        "compileall",
        "-q",
        "config.py",
        "app",
        "scripts",
        "tests",
        "migrations",
    ])

    contract_pytest = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests/architecture/test_phase2b_route_snapshot_contract.py",
        "-q",
        "-ra",
    ], timeout=900)

    quality_smoke = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests/quality",
        "-m",
        "ci_safe",
        "-q",
        "-ra",
    ], timeout=900)

    default_pytest = run_cmd([
        str(py),
        "-m",
        "pytest",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ], timeout=1800)

    phase2c1_rerun = run_cmd([
        str(py),
        "scripts/quality/bys360_phase2c1_wildcard_import_explicit_plan.py",
    ], timeout=1800)

    return {
        "compileall_returncode": compile_result["returncode"],
        "contract_pytest_returncode": contract_pytest["returncode"],
        "contract_pytest_summary": parse_pytest_summary(contract_pytest["combined_tail"]),
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": parse_pytest_summary(quality_smoke["combined_tail"]),
        "pytest_default_returncode": default_pytest["returncode"],
        "pytest_default_summary": parse_pytest_summary(default_pytest["combined_tail"]),
        "phase2c1_rerun_returncode": phase2c1_rerun["returncode"],
    }


def validation_green(validation: dict) -> bool:
    default_summary = validation["pytest_default_summary"]
    contract_summary = validation["contract_pytest_summary"]

    return (
        validation["compileall_returncode"] == 0
        and validation["contract_pytest_returncode"] == 0
        and validation["pytest_quality_smoke_returncode"] == 0
        and validation["pytest_default_returncode"] == 0
        and validation["phase2c1_rerun_returncode"] == 0
        and contract_summary.get("failed", 0) == 0
        and contract_summary.get("errors", 0) == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and default_summary.get("passed", 0) >= 700
    )


def main() -> int:
    ARCH.mkdir(parents=True, exist_ok=True)
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    plan = read_json(PLAN_JSON)
    candidates = get_candidates(plan)

    before_all_wildcards = count_all_wildcards()
    before_mobile_shared_wildcards = count_mobile_shared_wildcards()

    backups = []
    operations = []

    for item in candidates:
        path = ROOT / item["file"]
        if not path.exists():
            operations.append({
                "file": item["file"],
                "changed": False,
                "reason": "file_missing",
            })
            continue

        backup_path = backup_file(path)
        backups.append({
            "relative_path": item["file"],
            "backup_path": str(backup_path),
        })

        operations.append(replace_import_line(item))

    write_restore_script(backups)

    after_apply_all_wildcards = count_all_wildcards()
    after_apply_mobile_shared_wildcards = count_mobile_shared_wildcards()

    validation = run_validation()
    rollback_performed = False
    rollback_validation = None

    changed_count = sum(1 for item in operations if item.get("changed"))
    operation_error_count = sum(1 for item in operations if not item.get("changed"))

    expected_reduction = changed_count
    actual_reduction = before_all_wildcards - after_apply_all_wildcards
    mobile_shared_reduction = before_mobile_shared_wildcards - after_apply_mobile_shared_wildcards

    should_rollback = (
        operation_error_count > 0
        or actual_reduction != expected_reduction
        or not validation_green(validation)
    )

    if should_rollback:
        rollback_performed = True
        restore_backups(backups)
        rollback_validation = run_validation()

    final_all_wildcards = count_all_wildcards()
    final_mobile_shared_wildcards = count_mobile_shared_wildcards()

    final_phase2c1 = read_json(PLAN_JSON)

    ok = (
        rollback_performed is False
        and operation_error_count == 0
        and changed_count == len(candidates)
        and actual_reduction == expected_reduction
        and mobile_shared_reduction == expected_reduction
        and validation_green(validation)
        and final_all_wildcards == before_all_wildcards - changed_count
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2C2_MOBILE_SHARED_WILDCARD_IMPORT_APPLY",
        "mode": "safe_apply_with_backup_and_auto_rollback",
        "ok": ok,
        "decision": "PHASE2C2_GREEN" if ok else "PHASE2C2_ROLLBACK_OR_REVIEW_REQUIRED",
        "backup_root": str(BACKUP_ROOT),
        "restore_script": str(RESTORE_PS1),
        "candidate_count": len(candidates),
        "changed_count": changed_count,
        "operation_error_count": operation_error_count,
        "before_all_wildcards": before_all_wildcards,
        "after_apply_all_wildcards": after_apply_all_wildcards,
        "final_all_wildcards": final_all_wildcards,
        "before_mobile_shared_wildcards": before_mobile_shared_wildcards,
        "after_apply_mobile_shared_wildcards": after_apply_mobile_shared_wildcards,
        "final_mobile_shared_wildcards": final_mobile_shared_wildcards,
        "expected_reduction": expected_reduction,
        "actual_reduction": actual_reduction,
        "mobile_shared_reduction": mobile_shared_reduction,
        "rollback_performed": rollback_performed,
        "operations": operations,
        "validation": validation,
        "rollback_validation": rollback_validation,
        "phase2c1_after": {
            "wildcard_import_count": final_phase2c1.get("wildcard_import_count"),
            "ready_for_explicit_import_count": final_phase2c1.get("ready_for_explicit_import_count"),
            "manual_review_count": final_phase2c1.get("manual_review_count"),
            "first_apply_candidate_count": final_phase2c1.get("first_apply_candidate_count"),
            "ok": final_phase2c1.get("ok"),
        },
        "next_action": "Faz 2C3 ikinci düşük riskli wildcard import paketi planlanabilir." if ok else "Rapor incelenmeli; rollback yapıldıysa dosyalar eski halindedir.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2C2 Mobile Shared Wildcard Import Apply",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Backup root: `{result['backup_root']}`",
        f"- Restore script: `{result['restore_script']}`",
        f"- Candidate count: {result['candidate_count']}",
        f"- Changed count: {result['changed_count']}",
        f"- Operation error count: {result['operation_error_count']}",
        f"- Before all wildcards: {result['before_all_wildcards']}",
        f"- Final all wildcards: {result['final_all_wildcards']}",
        f"- Before mobile shared wildcards: {result['before_mobile_shared_wildcards']}",
        f"- Final mobile shared wildcards: {result['final_mobile_shared_wildcards']}",
        f"- Expected reduction: {result['expected_reduction']}",
        f"- Actual reduction: {result['actual_reduction']}",
        f"- Rollback performed: {result['rollback_performed']}",
        f"- Compileall returncode: {validation['compileall_returncode']}",
        f"- Contract pytest returncode: {validation['contract_pytest_returncode']}",
        f"- Pytest quality smoke returncode: {validation['pytest_quality_smoke_returncode']}",
        f"- Pytest default returncode: {validation['pytest_default_returncode']}",
        f"- Phase2C1 rerun returncode: {validation['phase2c1_rerun_returncode']}",
        "",
        "## Operations",
        "",
        "```json",
        json.dumps(operations, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Validation",
        "",
        "```json",
        json.dumps(validation, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Phase2C1 After",
        "",
        "```json",
        json.dumps(result["phase2c1_after"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("PHASE2C2_REPORT_JSON:", OUT_JSON)
    print("PHASE2C2_REPORT_MD:", OUT_MD)
    print("PHASE2C2_BACKUP_ROOT:", BACKUP_ROOT)
    print("PHASE2C2_RESTORE_SCRIPT:", RESTORE_PS1)
    print("PHASE2C2_CANDIDATE_COUNT:", result["candidate_count"])
    print("PHASE2C2_CHANGED_COUNT:", result["changed_count"])
    print("PHASE2C2_OPERATION_ERROR_COUNT:", result["operation_error_count"])
    print("PHASE2C2_BEFORE_ALL_WILDCARDS:", result["before_all_wildcards"])
    print("PHASE2C2_FINAL_ALL_WILDCARDS:", result["final_all_wildcards"])
    print("PHASE2C2_BEFORE_MOBILE_SHARED_WILDCARDS:", result["before_mobile_shared_wildcards"])
    print("PHASE2C2_FINAL_MOBILE_SHARED_WILDCARDS:", result["final_mobile_shared_wildcards"])
    print("PHASE2C2_EXPECTED_REDUCTION:", result["expected_reduction"])
    print("PHASE2C2_ACTUAL_REDUCTION:", result["actual_reduction"])
    print("PHASE2C2_ROLLBACK_PERFORMED:", result["rollback_performed"])
    print("PHASE2C2_COMPILEALL_RETURN_CODE:", validation["compileall_returncode"])
    print("PHASE2C2_CONTRACT_PYTEST_RETURN_CODE:", validation["contract_pytest_returncode"])
    print("PHASE2C2_CONTRACT_PYTEST_SUMMARY:", json.dumps(validation["contract_pytest_summary"], ensure_ascii=False))
    print("PHASE2C2_PYTEST_QUALITY_SMOKE_RETURN_CODE:", validation["pytest_quality_smoke_returncode"])
    print("PHASE2C2_PYTEST_DEFAULT_RETURN_CODE:", validation["pytest_default_returncode"])
    print("PHASE2C2_PYTEST_DEFAULT_SUMMARY:", json.dumps(validation["pytest_default_summary"], ensure_ascii=False))
    print("PHASE2C2_PHASE2C1_RERUN_RETURN_CODE:", validation["phase2c1_rerun_returncode"])
    print("PHASE2C2_PHASE2C1_AFTER:", json.dumps(result["phase2c1_after"], ensure_ascii=False))
    print("PHASE2C2_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
