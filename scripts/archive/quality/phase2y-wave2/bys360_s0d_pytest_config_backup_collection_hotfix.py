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
QUALITY = ROOT / "reports" / "quality"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

PYTEST_INI = ROOT / "pytest.ini"
PYPROJECT = ROOT / "pyproject.toml"
BACKUP_ROOT = RELEASES / f"S0D_PYTEST_CONFIG_BACKUP_COLLECTION_HOTFIX_BACKUP_{STAMP}"

OUT_JSON = QUALITY / "BYS360_S0D_PYTEST_CONFIG_BACKUP_COLLECTION_HOTFIX.json"
OUT_MD = QUALITY / "BYS360_S0D_PYTEST_CONFIG_BACKUP_COLLECTION_HOTFIX.md"

S0A_SCRIPT = ROOT / "scripts" / "quality" / "bys360_s0a_claude_findings_verification_audit.py"
S0A_JSON = QUALITY / "BYS360_S0A_MAINTENANCE_FINDINGS_VERIFICATION_AUDIT.json"

BUILTIN_MARKERS = {
    "parametrize",
    "skip",
    "skipif",
    "xfail",
    "usefixtures",
    "filterwarnings",
    "tryfirst",
    "trylast",
}


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


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


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


def backup_file(path: Path) -> str | None:
    if not path.exists():
        return None

    rel = path.relative_to(ROOT)
    target = BACKUP_ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    return str(target)


def pytest_cov_available(py: Path) -> bool:
    result = run_cmd([str(py), "-m", "pytest", "--help"], timeout=180)
    return "--cov" in (result["stdout"] + result["stderr"])


def scan_pytest_markers() -> list[str]:
    markers = set()

    for root in [ROOT / "tests"]:
        if not root.exists():
            continue

        for path in root.rglob("*.py"):
            text = read_text(path)

            for marker in re.findall(r"pytest\.mark\.([A-Za-z_][A-Za-z0-9_]*)", text):
                if marker not in BUILTIN_MARKERS:
                    markers.add(marker)

            for marker in re.findall(r"@pytest\.mark\.([A-Za-z_][A-Za-z0-9_]*)", text):
                if marker not in BUILTIN_MARKERS:
                    markers.add(marker)

    markers.update({"ci_safe", "live", "realdb", "slow"})

    return sorted(markers)


def remove_pytest_section_from_pyproject(text: str) -> tuple[str, bool, list[str]]:
    lines = text.splitlines()
    start = None
    end = None

    for idx, line in enumerate(lines):
        if line.strip() == "[tool.pytest.ini_options]":
            start = idx
            break

    if start is None:
        return text, False, []

    end = len(lines)

    for idx in range(start + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("[") and stripped.endswith("]") and not stripped.startswith("[["):
            end = idx
            break

    removed = lines[start:end]
    new_lines = lines[:start] + lines[end:]

    while len(new_lines) >= 2 and new_lines[start - 1:start + 1] == ["", ""]:
        del new_lines[start]

    return "\n".join(new_lines).rstrip() + "\n", True, removed


def build_pytest_ini(markers: list[str], include_cov: bool) -> str:
    addopts = "--strict-markers --disable-warnings"

    if include_cov:
        addopts += " --cov=app.bootstrap --cov=app.security --cov=app.security_headers --cov=app.security_audit --cov-report=term-missing"

    marker_lines = []
    descriptions = {
        "ci_safe": "CI güvenli testler.",
        "live": "Canlı servis veya dış bağımlılık gerektiren testler.",
        "realdb": "Gerçek veritabanı gerektiren testler.",
        "slow": "Uzun süren testler.",
    }

    for marker in markers:
        marker_lines.append(f"    {marker}: {descriptions.get(marker, 'BYS360 test işaretleyicisi.')}")

    return "\n".join([
        "[pytest]",
        "minversion = 8.0",
        "testpaths = tests",
        "python_files = test_*.py",
        f"addopts = {addopts}",
        "norecursedirs =",
        "    .git",
        "    .venv",
        "    venv",
        "    .venv_old_*",
        "    venv_old_*",
        "    node_modules",
        "    __pycache__",
        "    .pytest_cache",
        "    .mypy_cache",
        "    reports",
        "    releases",
        "    archive",
        "    backups",
        "markers =",
        *marker_lines,
        "",
    ])


def check_config_state() -> dict:
    pytest_text = read_text(PYTEST_INI)
    pyproject_text = read_text(PYPROJECT)

    return {
        "pytest_ini_exists": PYTEST_INI.exists(),
        "pyproject_exists": PYPROJECT.exists(),
        "pyproject_has_tool_pytest_ini_options": "[tool.pytest.ini_options]" in pyproject_text,
        "pytest_ini_has_testpaths": bool(re.search(r"(?m)^testpaths\s*=\s*tests\s*$", pytest_text)),
        "pytest_ini_has_norecursedirs_reports": "reports" in pytest_text and "norecursedirs" in pytest_text,
        "pytest_ini_has_strict_markers": "--strict-markers" in pytest_text,
        "pytest_ini_has_disable_warnings": "--disable-warnings" in pytest_text,
        "pytest_ini_has_markers": bool(re.search(r"(?m)^markers\s*=", pytest_text)),
        "pytest_config_conflict_likely": PYTEST_INI.exists() and "[tool.pytest.ini_options]" in pyproject_text,
    }


def backup_test_dirs_exist() -> dict:
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
                test_files = list(tests_dir.rglob("test_*.py")) + list(tests_dir.rglob("*_test.py"))
                dirs.append({
                    "path": str(tests_dir.relative_to(ROOT)).replace("\\", "/"),
                    "test_file_count": len(test_files),
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
        "note": "Bu faz backup test klasörlerini silmez; pytest collection dışına alır.",
    }


def detect_backup_collection_hits(output: str) -> dict:
    patterns = [
        "reports/quality",
        "reports\\quality",
        "P2_BACKUP",
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


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    original_state = check_config_state()
    backup_paths = {
        "pytest_ini": backup_file(PYTEST_INI),
        "pyproject": backup_file(PYPROJECT),
    }

    markers = scan_pytest_markers()
    cov_available = pytest_cov_available(py)

    pytest_ini_new = build_pytest_ini(markers, include_cov=cov_available)
    pytest_ini_old = read_text(PYTEST_INI)

    pyproject_old = read_text(PYPROJECT)
    pyproject_new, pyproject_section_removed, removed_pyproject_pytest_lines = remove_pytest_section_from_pyproject(pyproject_old)

    operations = []

    if pytest_ini_old != pytest_ini_new:
        PYTEST_INI.write_text(pytest_ini_new, encoding="utf-8")
        operations.append({
            "type": "write_pytest_ini_single_source",
            "status": "patched",
            "include_cov": cov_available,
            "marker_count": len(markers),
        })

    if PYPROJECT.exists() and pyproject_section_removed:
        PYPROJECT.write_text(pyproject_new, encoding="utf-8")
        operations.append({
            "type": "remove_pyproject_pytest_ini_options_section",
            "status": "patched",
            "removed_line_count": len(removed_pyproject_pytest_lines),
        })

    post_state = check_config_state()
    backup_tests = backup_test_dirs_exist()

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
            "red_flag_count": s0a_json.get("red_flag_count"),
        }

    ok = (
        bool(operations)
        and post_state["pytest_config_conflict_likely"] is False
        and post_state["pytest_ini_has_testpaths"] is True
        and post_state["pytest_ini_has_norecursedirs_reports"] is True
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
        and s0a_rerun.get("pytest_config_conflict_likely") is False
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0D_PYTEST_CONFIG_BACKUP_COLLECTION_HOTFIX",
        "mode": "safe_config_change_with_backup_no_delete",
        "ok": ok,
        "decision": "S0D_GREEN" if ok else "S0D_REVIEW_REQUIRED",
        "backup_root": str(BACKUP_ROOT),
        "backup_paths": backup_paths,
        "operations": operations,
        "pytest_cov_available": cov_available,
        "marker_count": len(markers),
        "markers": markers,
        "original_state": original_state,
        "post_state": post_state,
        "backup_tests_detected_but_not_deleted": backup_tests,
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
        "next_action": "S0E backup test/report arşiv temizliği manifestli yapılabilir." if ok else "S0D raporu incelenmeli; gerekirse backup dosyalarından geri dönüş yapılmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 S0D Pytest Config ve Backup Collection Hotfix",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Backup root: `{result['backup_root']}`",
        f"- Operation count: {len(operations)}",
        f"- Pytest-cov available: {cov_available}",
        f"- Marker count: {len(markers)}",
        f"- Config conflict after: {post_state['pytest_config_conflict_likely']}",
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
        "## Post State",
        "",
        "```json",
        json.dumps(post_state, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Backup Tests Detected But Not Deleted",
        "",
        "```json",
        json.dumps(backup_tests, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Backup Collection Evidence",
        "",
        "```json",
        json.dumps(backup_collection, ensure_ascii=False, indent=2),
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

    print("S0D_REPORT_JSON:", OUT_JSON)
    print("S0D_REPORT_MD:", OUT_MD)
    print("S0D_BACKUP_ROOT:", BACKUP_ROOT)
    print("S0D_OPERATION_COUNT:", len(operations))
    print("S0D_PYTEST_COV_AVAILABLE:", cov_available)
    print("S0D_MARKER_COUNT:", len(markers))
    print("S0D_PYTEST_CONFIG_CONFLICT_AFTER:", post_state["pytest_config_conflict_likely"])
    print("S0D_BACKUP_TEST_DIR_COUNT_DETECTED_NOT_DELETED:", backup_tests["backup_test_dir_count"])
    print("S0D_BACKUP_COLLECTION_HIT_COUNT:", backup_collection["backup_collection_hit_count"])
    print("S0D_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0D_COLLECT_ONLY_RETURN_CODE:", result["collect_only_returncode"])
    print("S0D_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0D_PYTEST_FULL_RETURN_CODE:", result["pytest_full_returncode"])
    print("S0D_PYTEST_FULL_SUMMARY:", json.dumps(full_summary, ensure_ascii=False))
    print("S0D_PYTEST_DEFAULT_RETURN_CODE:", result["pytest_default_returncode"])
    print("S0D_PYTEST_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("S0D_S0A_PYTEST_CONFIG_CONFLICT_LIKELY:", s0a_rerun.get("pytest_config_conflict_likely"))
    print("S0D_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
