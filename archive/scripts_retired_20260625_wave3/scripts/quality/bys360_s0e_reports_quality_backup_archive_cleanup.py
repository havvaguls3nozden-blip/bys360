from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import hashlib
import json
import os
import re
import shutil
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

ARCHIVE_ROOT = RELEASES / f"S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_{STAMP}"
ARCHIVE_MOVED_ROOT = ARCHIVE_ROOT / "moved"

OUT_JSON = QUALITY / "BYS360_S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_CLEANUP.json"
OUT_MD = QUALITY / "BYS360_S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_CLEANUP.md"

S0A_SCRIPT = ROOT / "scripts" / "quality" / "bys360_s0a_claude_findings_verification_audit.py"
S0A_JSON = QUALITY / "BYS360_S0A_MAINTENANCE_FINDINGS_VERIFICATION_AUDIT.json"


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
            "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-24000:],
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
            "combined_tail": (stdout + "\n" + stderr + "\nTIMEOUT")[-24000:],
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
    return round(value / 1024 / 1024, 3)


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None

    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def count_files(path: Path) -> int:
    if not path.exists():
        return 0

    if path.is_file():
        return 1

    count = 0
    for item in path.rglob("*"):
        if item.is_file():
            count += 1

    return count


def count_test_files(path: Path) -> int:
    if not path.exists() or not path.is_dir():
        return 0

    tests = set()
    for item in path.rglob("test_*.py"):
        if item.is_file():
            tests.add(item)
    for item in path.rglob("*_test.py"):
        if item.is_file():
            tests.add(item)

    return len(tests)


def candidate_backup_dirs() -> list[Path]:
    if not QUALITY.exists():
        return []

    candidates = []

    for path in QUALITY.iterdir():
        if not path.is_dir():
            continue

        name = path.name.lower()

        if (
            "backup" in name
            or "backups" in name
            or "_bak" in name
            or path.name.upper() in {"P0_BACKUP", "P1_BACKUP", "P2_BACKUP"}
        ):
            candidates.append(path)

    candidates.sort(key=lambda p: p.as_posix().lower())
    return candidates


def manifest_for_dir(path: Path) -> dict:
    files = []

    if path.exists():
        for item in sorted(path.rglob("*")):
            if item.is_file():
                rel = item.relative_to(path).as_posix()
                files.append({
                    "relative_path": rel,
                    "size_bytes": item.stat().st_size if item.exists() else 0,
                    "sha256": sha256_file(item),
                })

    return {
        "source": str(path.relative_to(ROOT)).replace("\\", "/"),
        "file_count": len(files),
        "test_file_count": count_test_files(path),
        "size_bytes": size_bytes(path),
        "size_mb": mb(size_bytes(path)),
        "files_top_300": files[:300],
        "file_manifest_truncated": len(files) > 300,
    }


def detect_backup_test_dirs_under_project() -> dict:
    roots = [
        ROOT / "reports",
        ROOT / "reports" / "quality",
        ROOT / "backups",
        ROOT / "archive",
    ]

    dirs = []

    for root in roots:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_dir():
                continue

            low = str(path).lower()
            if "backup" not in low and "_bak" not in low:
                continue

            tests_dir = path / "tests"
            if tests_dir.exists() and tests_dir.is_dir():
                dirs.append({
                    "path": str(tests_dir.relative_to(ROOT)).replace("\\", "/"),
                    "test_file_count": count_test_files(tests_dir),
                    "size_mb": mb(size_bytes(tests_dir)),
                })

    unique = []
    seen = set()
    for item in dirs:
        key = item["path"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return {
        "backup_test_dir_count": len(unique),
        "backup_test_file_count": sum(item["test_file_count"] for item in unique),
        "backup_test_dirs": unique,
    }


def detect_quality_backup_dirs_under_project() -> dict:
    if not QUALITY.exists():
        return {
            "quality_backup_dir_count": 0,
            "quality_backup_total_mb": 0,
            "quality_backup_dirs": [],
        }

    dirs = []

    for path in QUALITY.rglob("*"):
        if not path.is_dir():
            continue

        low_name = path.name.lower()
        low_full = str(path).lower()

        if "backup" in low_name or "backups" in low_full or "_bak" in low_name:
            dirs.append({
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "size_mb": mb(size_bytes(path)),
            })

    unique = []
    seen = set()
    for item in dirs:
        key = item["path"]
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return {
        "quality_backup_dir_count": len(unique),
        "quality_backup_total_mb": round(sum(item["size_mb"] for item in unique), 3),
        "quality_backup_dirs": unique,
    }


def detect_backup_collection_hits(output: str) -> dict:
    patterns = [
        "reports/quality",
        "reports\\quality",
        "P2_BACKUP",
        "P0_BACKUP",
        "a5_p1_archive_marker_safe_v1_backups",
        "_archive_a5_obsolete",
    ]

    hits = []
    for pattern in patterns:
        if pattern in output:
            hits.append(pattern)

    return {
        "backup_collection_hit_count": len(hits),
        "backup_collection_hits": hits,
    }


def move_candidates(candidates: list[Path]) -> tuple[list[dict], list[dict]]:
    operations = []
    errors = []

    ARCHIVE_MOVED_ROOT.mkdir(parents=True, exist_ok=True)

    for src in candidates:
        if not src.exists():
            continue

        rel = src.relative_to(ROOT)
        dst = ARCHIVE_MOVED_ROOT / rel

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)

            before = manifest_for_dir(src)
            shutil.move(str(src), str(dst))

            after = {
                "destination": str(dst),
                "destination_exists": dst.exists(),
                "source_exists_after_move": src.exists(),
                "destination_file_count": count_files(dst),
                "destination_test_file_count": count_test_files(dst),
                "destination_size_mb": mb(size_bytes(dst)),
            }

            operations.append({
                "type": "move_reports_quality_backup_dir_to_release_archive",
                "status": "moved",
                "source": str(rel).replace("\\", "/"),
                "destination": str(dst),
                "before": before,
                "after": after,
            })

        except Exception as exc:
            errors.append({
                "source": str(src.relative_to(ROOT)).replace("\\", "/"),
                "error": str(exc),
            })

    return operations, errors


def write_restore_script(operations: list[dict]) -> Path:
    restore_path = ARCHIVE_ROOT / "RESTORE_S0E_REPORTS_QUALITY_BACKUPS.ps1"

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

    lines.append('Write-Host "S0E restore tamamlandı."')

    restore_path.write_text("\n".join(lines), encoding="utf-8")
    return restore_path


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)

    candidates = candidate_backup_dirs()

    before_backup_tests = detect_backup_test_dirs_under_project()
    before_quality_backups = detect_quality_backup_dirs_under_project()

    pre_manifest = {
        "candidate_count": len(candidates),
        "candidates": [manifest_for_dir(path) for path in candidates],
        "before_backup_tests": before_backup_tests,
        "before_quality_backups": before_quality_backups,
    }

    operations, errors = move_candidates(candidates)
    restore_script = write_restore_script(operations)

    after_backup_tests = detect_backup_test_dirs_under_project()
    after_quality_backups = detect_quality_backup_dirs_under_project()

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

    collect_result = run_cmd([
        str(py),
        "-m",
        "pytest",
        "--collect-only",
        "-q",
    ], timeout=900)

    backup_collection = detect_backup_collection_hits(
        (collect_result["stdout"] or "") + "\n" + (collect_result["stderr"] or "")
    )

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
            "config_exc_bug_likely": (
                s0a_json.get("checks", {})
                .get("config_exc_bug", {})
                .get("bug_likely")
            ),
            "pytest_config_conflict_likely": (
                s0a_json.get("checks", {})
                .get("pytest_config", {})
                .get("conflict_likely")
            ),
            "backup_test_dir_count": (
                s0a_json.get("checks", {})
                .get("backup_tests", {})
                .get("backup_test_dir_count")
            ),
            "quality_backup_dir_count": (
                s0a_json.get("checks", {})
                .get("quality_backup_dirs", {})
                .get("quality_backup_dir_count")
            ),
            "old_venv_total_mb": (
                s0a_json.get("checks", {})
                .get("old_venvs", {})
                .get("old_venv_total_mb")
            ),
            "pip_audit_vulnerability_count": (
                s0a_json.get("checks", {})
                .get("pip_audit", {})
                .get("vulnerability_count")
            ),
        }

    ok = (
        len(errors) == 0
        and len(operations) == len(candidates)
        and compile_result["returncode"] == 0
        and collect_result["returncode"] == 0
        and backup_collection["backup_collection_hit_count"] == 0
        and quality_smoke["returncode"] == 0
        and full_pytest["returncode"] == 0
        and default_pytest["returncode"] == 0
        and full_summary.get("failed", 0) == 0
        and full_summary.get("errors", 0) == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and full_summary.get("passed", 0) >= 700
        and default_summary.get("passed", 0) >= 700
        and after_backup_tests["backup_test_dir_count"] == 0
        and after_quality_backups["quality_backup_dir_count"] == 0
        and s0a_rerun.get("backup_test_dir_count") in {0, None}
        and s0a_rerun.get("quality_backup_dir_count") in {0, None}
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_CLEANUP",
        "mode": "move_to_release_archive_with_manifest_no_delete",
        "ok": ok,
        "decision": "S0E_GREEN" if ok else "S0E_REVIEW_REQUIRED",
        "archive_root": str(ARCHIVE_ROOT),
        "restore_script": str(restore_script),
        "pre_manifest": pre_manifest,
        "operation_count": len(operations),
        "operations": operations,
        "errors": errors,
        "after_backup_tests": after_backup_tests,
        "after_quality_backups": after_quality_backups,
        "backup_collection": backup_collection,
        "compileall_returncode": compile_result["returncode"],
        "collect_only_returncode": collect_result["returncode"],
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": quality_summary,
        "pytest_full_returncode": full_pytest["returncode"],
        "pytest_full_summary": full_summary,
        "pytest_default_returncode": default_pytest["returncode"],
        "pytest_default_summary": default_summary,
        "s0a_rerun": s0a_rerun,
        "next_action": "S0F pip-audit bağımlılık güncellemelerine geçilebilir." if ok else "S0E raporu incelenmeli; gerekirse restore script ile geri alınmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 S0E Reports/Quality Backup Archive Cleanup",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Archive root: `{result['archive_root']}`",
        f"- Restore script: `{result['restore_script']}`",
        f"- Candidate count: {pre_manifest['candidate_count']}",
        f"- Operation count: {result['operation_count']}",
        f"- Error count: {len(errors)}",
        f"- Backup test dir count after: {after_backup_tests['backup_test_dir_count']}",
        f"- Quality backup dir count after: {after_quality_backups['quality_backup_dir_count']}",
        f"- Backup collection hit count: {backup_collection['backup_collection_hit_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Collect-only returncode: {result['collect_only_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        f"- Pytest full returncode: {result['pytest_full_returncode']}",
        f"- Pytest default returncode: {result['pytest_default_returncode']}",
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
        "## After Backup Tests",
        "",
        "```json",
        json.dumps(after_backup_tests, ensure_ascii=False, indent=2),
        "```",
        "",
        "## After Quality Backups",
        "",
        "```json",
        json.dumps(after_quality_backups, ensure_ascii=False, indent=2),
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

    print("S0E_REPORT_JSON:", OUT_JSON)
    print("S0E_REPORT_MD:", OUT_MD)
    print("S0E_ARCHIVE_ROOT:", ARCHIVE_ROOT)
    print("S0E_RESTORE_SCRIPT:", restore_script)
    print("S0E_CANDIDATE_COUNT:", pre_manifest["candidate_count"])
    print("S0E_OPERATION_COUNT:", result["operation_count"])
    print("S0E_ERROR_COUNT:", len(errors))
    print("S0E_BACKUP_TEST_DIR_COUNT_AFTER:", after_backup_tests["backup_test_dir_count"])
    print("S0E_QUALITY_BACKUP_DIR_COUNT_AFTER:", after_quality_backups["quality_backup_dir_count"])
    print("S0E_BACKUP_COLLECTION_HIT_COUNT:", backup_collection["backup_collection_hit_count"])
    print("S0E_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0E_COLLECT_ONLY_RETURN_CODE:", result["collect_only_returncode"])
    print("S0E_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0E_PYTEST_FULL_RETURN_CODE:", result["pytest_full_returncode"])
    print("S0E_PYTEST_FULL_SUMMARY:", json.dumps(full_summary, ensure_ascii=False))
    print("S0E_PYTEST_DEFAULT_RETURN_CODE:", result["pytest_default_returncode"])
    print("S0E_PYTEST_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("S0E_S0A_BACKUP_TEST_DIR_COUNT:", s0a_rerun.get("backup_test_dir_count"))
    print("S0E_S0A_QUALITY_BACKUP_DIR_COUNT:", s0a_rerun.get("quality_backup_dir_count"))
    print("S0E_S0A_RED_FLAG_COUNT:", s0a_rerun.get("red_flag_count"))
    print("S0E_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
