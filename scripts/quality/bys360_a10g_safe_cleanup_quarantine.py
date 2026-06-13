from pathlib import Path
from datetime import datetime
import json
import shutil
import subprocess
import os
import re

ROOT = Path(".").resolve()
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

A10F_JSON = Path("reports/quality/BYS360_A10F_CLEANUP_CANDIDATE_PRECISION_PLAN.json")
OUT_JSON = Path("reports/quality/BYS360_A10G_SAFE_CLEANUP_QUARANTINE_DECISION.json")
OUT_MD = Path("reports/quality/BYS360_A10G_SAFE_CLEANUP_QUARANTINE_DECISION.md")

QUARANTINE_ROOT = RELEASES / f"A10G_SAFE_CLEANUP_QUARANTINE_{STAMP}"

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def run_cmd(cmd, timeout=1200):
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
        "stdout_tail": (proc.stdout or "")[-6000:],
        "stderr_tail": (proc.stderr or "")[-6000:],
        "combined": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-12000:],
    }

def parse_pytest_summary(text: str):
    summary = {}
    for num, key in re.findall(r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warnings|warning)", text or ""):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)
    return summary

def move_candidate(rel_path: str):
    src = ROOT / rel_path
    dst = QUARANTINE_ROOT / rel_path

    if not src.exists():
        return {
            "path": rel_path,
            "status": "missing_before_move",
        }

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

    return {
        "path": rel_path,
        "status": "moved",
        "to": str(dst),
    }

def main():
    if not A10F_JSON.exists():
        raise SystemExit("A10F raporu bulunamadı. Önce A10F çalışmalı.")

    a10f = read_json(A10F_JSON)
    safe_candidates = a10f.get("safe_quarantine_candidates", [])

    QUARANTINE_ROOT.mkdir(parents=True, exist_ok=True)

    moved = []
    for item in safe_candidates:
        rel_path = item.get("path")
        if rel_path:
            moved.append(move_candidate(rel_path))

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
    ])

    # Audit zincirini tekrar üret
    a10a_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "scripts/quality/bys360_a10a_phase_dev_debug_audit.py",
    ])

    a10b_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "scripts/quality/bys360_a10b_phase_dev_debug_precision_audit.py",
    ])

    a10f_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "scripts/quality/bys360_a10f_cleanup_candidate_precision_plan.py",
    ])

    refreshed_a10f = {}
    refreshed_a10f_path = Path("reports/quality/BYS360_A10F_CLEANUP_CANDIDATE_PRECISION_PLAN.json")
    if refreshed_a10f_path.exists():
        refreshed_a10f = read_json(refreshed_a10f_path)

    pytest_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ], timeout=1800)

    pytest_summary = parse_pytest_summary(pytest_result["combined"])

    moved_count = sum(1 for x in moved if x.get("status") == "moved")
    missing_count = sum(1 for x in moved if x.get("status") == "missing_before_move")
    after_safe_count = refreshed_a10f.get("safe_quarantine_candidate_count")

    ok = (
        moved_count == len(safe_candidates)
        and missing_count == 0
        and compile_result["returncode"] == 0
        and a10a_result["returncode"] == 0
        and a10b_result["returncode"] == 0
        and a10f_result["returncode"] == 0
        and after_safe_count == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10G_SAFE_CLEANUP_QUARANTINE",
        "ok": ok,
        "decision": "A10G_SAFE_CLEANUP_QUARANTINE_GREEN" if ok else "A10G_SAFE_CLEANUP_QUARANTINE_NOT_GREEN",
        "quarantine_root": str(QUARANTINE_ROOT),
        "source_a10f": str(A10F_JSON),
        "safe_candidate_count_before": len(safe_candidates),
        "moved_count": moved_count,
        "missing_before_move_count": missing_count,
        "moved": moved[:500],
        "compileall_returncode": compile_result["returncode"],
        "a10a_returncode": a10a_result["returncode"],
        "a10b_returncode": a10b_result["returncode"],
        "a10f_returncode": a10f_result["returncode"],
        "safe_quarantine_candidate_count_after": after_safe_count,
        "cleanup_candidate_count_after": refreshed_a10f.get("cleanup_candidate_count"),
        "keep_or_review_count_after": refreshed_a10f.get("keep_or_review_count"),
        "a10f_by_decision_after": refreshed_a10f.get("by_decision"),
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "pytest_tail": pytest_result["combined"],
        "note": "Yalnızca A10F safe_quarantine_candidate sınıfı taşındı. Runtime, template, mobile, migration ve referans alan dosyalara dokunulmadı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10G Güvenli Cleanup Karantina Kararı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Quarantine root: `{result['quarantine_root']}`",
        f"- Safe candidate count before: {result['safe_candidate_count_before']}",
        f"- Moved count: {result['moved_count']}",
        f"- Missing before move count: {result['missing_before_move_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- A10A returncode: {result['a10a_returncode']}",
        f"- A10B returncode: {result['a10b_returncode']}",
        f"- A10F returncode: {result['a10f_returncode']}",
        f"- Safe quarantine candidate count after: {result['safe_quarantine_candidate_count_after']}",
        f"- Cleanup candidate count after: {result['cleanup_candidate_count_after']}",
        f"- Keep or review count after: {result['keep_or_review_count_after']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## Pytest Özeti",
        "",
        "```json",
        json.dumps(result["pytest_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## A10F Son Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["a10f_by_decision_after"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        result["note"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10G_REPORT_JSON:", OUT_JSON)
    print("A10G_REPORT_MD:", OUT_MD)
    print("A10G_QUARANTINE_ROOT:", QUARANTINE_ROOT)
    print("A10G_SAFE_CANDIDATE_COUNT_BEFORE:", result["safe_candidate_count_before"])
    print("A10G_MOVED_COUNT:", result["moved_count"])
    print("A10G_MISSING_BEFORE_MOVE_COUNT:", result["missing_before_move_count"])
    print("A10G_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A10G_SAFE_QUARANTINE_CANDIDATE_COUNT_AFTER:", result["safe_quarantine_candidate_count_after"])
    print("A10G_CLEANUP_CANDIDATE_COUNT_AFTER:", result["cleanup_candidate_count_after"])
    print("A10G_KEEP_OR_REVIEW_COUNT_AFTER:", result["keep_or_review_count_after"])
    print("A10G_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A10G_PYTEST_SUMMARY:", json.dumps(result["pytest_summary"], ensure_ascii=False))
    print("A10G_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
