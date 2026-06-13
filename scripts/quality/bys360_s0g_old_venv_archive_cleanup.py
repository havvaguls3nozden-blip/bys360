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

ARCHIVE_ROOT = RELEASES / f"S0G_OLD_VENV_ARCHIVE_{STAMP}"
ARCHIVE_MOVED_ROOT = ARCHIVE_ROOT / "moved"

OUT_JSON = QUALITY / "BYS360_S0G_OLD_VENV_ARCHIVE_CLEANUP.json"
OUT_MD = QUALITY / "BYS360_S0G_OLD_VENV_ARCHIVE_CLEANUP.md"
RESTORE_PS1 = ARCHIVE_ROOT / "RESTORE_S0G_OLD_VENV.ps1"

S0A_SCRIPT = ROOT / "scripts" / "quality" / "bys360_s0a_claude_findings_verification_audit.py"
S0A_JSON = QUALITY / "BYS360_S0A_CLAUDE_FINDINGS_VERIFICATION_AUDIT.json"


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


def size_bytes(path: Path) -> int:
    if not path.exists():
        return 0

    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0

    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            pass

    return total


def mb(value: int) -> float:
    return round(value / 1024 / 1024, 2)


def count_files(path: Path) -> int:
    if not path.exists():
        return 0

    if path.is_file():
        return 1

    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += 1
        except OSError:
            pass

    return total


def count_dirs(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0

    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_dir():
                total += 1
        except OSError:
            pass

    return total


def find_old_venv_dirs() -> list[Path]:
    candidates = []

    for path in ROOT.iterdir():
        if not path.is_dir():
            continue

        name = path.name.lower()

        if name == ".venv":
            continue

        if (
            name.startswith(".venv_old")
            or name.startswith("venv_old")
            or name.startswith(".venv-backup")
            or name.startswith("venv-backup")
        ):
            candidates.append(path)

    return sorted(candidates, key=lambda p: p.name.lower())


def old_venv_state() -> dict:
    dirs = find_old_venv_dirs()

    rows = []
    for path in dirs:
        rows.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "file_count": count_files(path),
            "dir_count": count_dirs(path),
            "size_mb": mb(size_bytes(path)),
        })

    return {
        "old_venv_dir_count": len(rows),
        "old_venv_total_mb": round(sum(item["size_mb"] for item in rows), 2),
        "old_venv_dirs": rows,
    }


def move_old_venvs(candidates: list[Path]) -> tuple[list[dict], list[dict]]:
    operations = []
    errors = []

    ARCHIVE_MOVED_ROOT.mkdir(parents=True, exist_ok=True)

    for src in candidates:
        rel = src.relative_to(ROOT)
        dst = ARCHIVE_MOVED_ROOT / rel

        try:
            before = {
                "source": str(rel).replace("\\", "/"),
                "file_count": count_files(src),
                "dir_count": count_dirs(src),
                "size_mb": mb(size_bytes(src)),
            }

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))

            after = {
                "destination": str(dst),
                "destination_exists": dst.exists(),
                "source_exists_after_move": src.exists(),
                "destination_file_count": count_files(dst),
                "destination_dir_count": count_dirs(dst),
                "destination_size_mb": mb(size_bytes(dst)),
            }

            operations.append({
                "type": "move_old_venv_to_release_archive",
                "status": "moved",
                "source": str(rel).replace("\\", "/"),
                "destination": str(dst),
                "before": before,
                "after": after,
            })

        except Exception as exc:
            errors.append({
                "source": str(rel).replace("\\", "/"),
                "error": str(exc),
            })

    return operations, errors


def write_restore_script(operations: list[dict]) -> None:
    lines = [
        '$ErrorActionPreference = "Stop"',
        'Set-Location "C:\\bys360\\project"',
        "",
    ]

    for op in operations:
        src = op["source"]
        dst = op["destination"]
        lines.extend([
            f'if (Test-Path -LiteralPath "{dst}") {{',
            f'  $target = Join-Path "C:\\bys360\\project" "{src}"',
            '  $parent = Split-Path -Parent $target',
            '  if (!(Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }',
            f'  Move-Item -LiteralPath "{dst}" -Destination $target -Force',
            '}',
            "",
        ])

    lines.append('Write-Host "S0G old venv restore tamamlandı."')
    RESTORE_PS1.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)

    before_state = old_venv_state()
    candidates = find_old_venv_dirs()

    operations, errors = move_old_venvs(candidates)
    write_restore_script(operations)

    after_state = old_venv_state()

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
    ], timeout=900)

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
    ], timeout=1800)

    default_pytest = run_cmd([
        str(py),
        "-m",
        "pytest",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ], timeout=1800)

    quality_summary = parse_pytest_summary(quality_smoke["combined_tail"])
    full_summary = parse_pytest_summary(full_pytest["combined_tail"])
    default_summary = parse_pytest_summary(default_pytest["combined_tail"])

    s0a_rerun = {"returncode": None}
    if S0A_SCRIPT.exists():
        s0a_proc = run_cmd([str(py), str(S0A_SCRIPT)], timeout=1200)
        s0a_json = read_json(S0A_JSON)
        s0a_rerun = {
            "returncode": s0a_proc["returncode"],
            "ok": s0a_json.get("ok"),
            "red_flag_count": s0a_json.get("red_flag_count"),
            "pip_audit_available": (
                s0a_json.get("checks", {})
                .get("pip_audit", {})
                .get("available")
            ),
            "pip_audit_vulnerability_count": (
                s0a_json.get("checks", {})
                .get("pip_audit", {})
                .get("vulnerability_count")
            ),
            "old_venv_dir_count": (
                s0a_json.get("checks", {})
                .get("old_venvs", {})
                .get("old_venv_dir_count")
            ),
            "old_venv_total_mb": (
                s0a_json.get("checks", {})
                .get("old_venvs", {})
                .get("old_venv_total_mb")
            ),
        }

    ok = (
        len(errors) == 0
        and len(operations) == len(candidates)
        and after_state["old_venv_dir_count"] == 0
        and compile_result["returncode"] == 0
        and quality_smoke["returncode"] == 0
        and full_pytest["returncode"] == 0
        and default_pytest["returncode"] == 0
        and full_summary.get("failed", 0) == 0
        and full_summary.get("errors", 0) == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and full_summary.get("passed", 0) >= 700
        and default_summary.get("passed", 0) >= 700
        and s0a_rerun.get("pip_audit_vulnerability_count") in {0, None}
        and s0a_rerun.get("old_venv_total_mb") in {0, 0.0, None}
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0G_OLD_VENV_ARCHIVE_CLEANUP",
        "mode": "move_old_venv_to_release_archive_no_delete",
        "ok": ok,
        "decision": "S0G_GREEN" if ok else "S0G_REVIEW_REQUIRED",
        "archive_root": str(ARCHIVE_ROOT),
        "restore_script": str(RESTORE_PS1),
        "candidate_count": len(candidates),
        "before_state": before_state,
        "operation_count": len(operations),
        "operations": operations,
        "errors": errors,
        "after_state": after_state,
        "compileall_returncode": compile_result["returncode"],
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": quality_summary,
        "pytest_full_returncode": full_pytest["returncode"],
        "pytest_full_summary": full_summary,
        "pytest_default_returncode": default_pytest["returncode"],
        "pytest_default_summary": default_summary,
        "s0a_rerun": s0a_rerun,
        "next_action": "S0Z final güvenlik/test hijyen kapanış raporu üretilebilir." if ok else "S0G raporu incelenmeli; gerekirse restore script ile geri alınmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 S0G Old Venv Archive Cleanup",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Archive root: `{result['archive_root']}`",
        f"- Restore script: `{result['restore_script']}`",
        f"- Candidate count: {result['candidate_count']}",
        f"- Operation count: {result['operation_count']}",
        f"- Error count: {len(errors)}",
        f"- Old venv dir count before: {before_state['old_venv_dir_count']}",
        f"- Old venv total MB before: {before_state['old_venv_total_mb']}",
        f"- Old venv dir count after: {after_state['old_venv_dir_count']}",
        f"- Old venv total MB after: {after_state['old_venv_total_mb']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        f"- Pytest full returncode: {result['pytest_full_returncode']}",
        f"- Pytest default returncode: {result['pytest_default_returncode']}",
        "",
        "## Before State",
        "",
        "```json",
        json.dumps(before_state, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Operations",
        "",
        "```json",
        json.dumps(operations, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Errors",
        "",
        "```json",
        json.dumps(errors, ensure_ascii=False, indent=2),
        "```",
        "",
        "## After State",
        "",
        "```json",
        json.dumps(after_state, ensure_ascii=False, indent=2),
        "```",
        "",
        "## S0A Rerun",
        "",
        "```json",
        json.dumps(s0a_rerun, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Full Summary",
        "",
        "```json",
        json.dumps(full_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Default Summary",
        "",
        "```json",
        json.dumps(default_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("S0G_REPORT_JSON:", OUT_JSON)
    print("S0G_REPORT_MD:", OUT_MD)
    print("S0G_ARCHIVE_ROOT:", ARCHIVE_ROOT)
    print("S0G_RESTORE_SCRIPT:", RESTORE_PS1)
    print("S0G_CANDIDATE_COUNT:", len(candidates))
    print("S0G_OPERATION_COUNT:", len(operations))
    print("S0G_ERROR_COUNT:", len(errors))
    print("S0G_OLD_VENV_DIR_COUNT_BEFORE:", before_state["old_venv_dir_count"])
    print("S0G_OLD_VENV_TOTAL_MB_BEFORE:", before_state["old_venv_total_mb"])
    print("S0G_OLD_VENV_DIR_COUNT_AFTER:", after_state["old_venv_dir_count"])
    print("S0G_OLD_VENV_TOTAL_MB_AFTER:", after_state["old_venv_total_mb"])
    print("S0G_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0G_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0G_PYTEST_FULL_RETURN_CODE:", result["pytest_full_returncode"])
    print("S0G_PYTEST_FULL_SUMMARY:", json.dumps(full_summary, ensure_ascii=False))
    print("S0G_PYTEST_DEFAULT_RETURN_CODE:", result["pytest_default_returncode"])
    print("S0G_PYTEST_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("S0G_S0A_RED_FLAG_COUNT:", s0a_rerun.get("red_flag_count"))
    print("S0G_S0A_PIP_AUDIT_VULNERABILITY_COUNT:", s0a_rerun.get("pip_audit_vulnerability_count"))
    print("S0G_S0A_OLD_VENV_TOTAL_MB:", s0a_rerun.get("old_venv_total_mb"))
    print("S0G_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
