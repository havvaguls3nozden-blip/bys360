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

OUT_JSON = Path("reports/quality/BYS360_A10H_ITERATIVE_SAFE_CLEANUP_DECISION.json")
OUT_MD = Path("reports/quality/BYS360_A10H_ITERATIVE_SAFE_CLEANUP_DECISION.md")

QUARANTINE_ROOT = RELEASES / f"A10H_ITERATIVE_SAFE_CLEANUP_QUARANTINE_{STAMP}"

A10F_JSON = Path("reports/quality/BYS360_A10F_CLEANUP_CANDIDATE_PRECISION_PLAN.json")

MAX_ROUNDS = 5

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
        "combined": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-12000:],
    }

def refresh_a10_chain():
    a10a = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "scripts/quality/bys360_a10a_phase_dev_debug_audit.py",
    ])

    a10b = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "scripts/quality/bys360_a10b_phase_dev_debug_precision_audit.py",
    ])

    a10f = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "scripts/quality/bys360_a10f_cleanup_candidate_precision_plan.py",
    ])

    return a10a, a10b, a10f

def move_candidate(rel_path: str, round_no: int):
    src = ROOT / rel_path
    dst = QUARANTINE_ROOT / f"round_{round_no}" / rel_path

    if not src.exists():
        return {
            "path": rel_path,
            "status": "missing_before_move",
            "round": round_no,
        }

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

    return {
        "path": rel_path,
        "status": "moved",
        "round": round_no,
        "to": str(dst),
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

def main():
    QUARANTINE_ROOT.mkdir(parents=True, exist_ok=True)

    rounds = []
    all_moves = []

    for round_no in range(1, MAX_ROUNDS + 1):
        a10a, a10b, a10f_run = refresh_a10_chain()

        if not A10F_JSON.exists():
            raise SystemExit("A10F raporu bulunamadı.")

        a10f = read_json(A10F_JSON)
        safe_candidates = a10f.get("safe_quarantine_candidates", [])
        before_safe = len(safe_candidates)

        round_info = {
            "round": round_no,
            "a10a_returncode": a10a["returncode"],
            "a10b_returncode": a10b["returncode"],
            "a10f_returncode": a10f_run["returncode"],
            "safe_candidate_count_before": before_safe,
            "moved_count": 0,
            "missing_count": 0,
            "cleanup_candidate_count": a10f.get("cleanup_candidate_count"),
            "keep_or_review_count": a10f.get("keep_or_review_count"),
            "by_decision": a10f.get("by_decision"),
        }

        if before_safe == 0:
            rounds.append(round_info)
            break

        moves = []
        for item in safe_candidates:
            rel_path = item.get("path")
            if rel_path:
                move = move_candidate(rel_path, round_no)
                moves.append(move)
                all_moves.append(move)

        round_info["moved_count"] = sum(1 for x in moves if x.get("status") == "moved")
        round_info["missing_count"] = sum(1 for x in moves if x.get("status") == "missing_before_move")
        rounds.append(round_info)

    # Son zinciri tekrar yenile
    final_a10a, final_a10b, final_a10f_run = refresh_a10_chain()
    final_a10f = read_json(A10F_JSON) if A10F_JSON.exists() else {}

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
    ])

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

    final_safe = final_a10f.get("safe_quarantine_candidate_count")
    moved_total = sum(1 for x in all_moves if x.get("status") == "moved")
    missing_total = sum(1 for x in all_moves if x.get("status") == "missing_before_move")

    ok = (
        missing_total == 0
        and final_safe == 0
        and compile_result["returncode"] == 0
        and final_a10a["returncode"] == 0
        and final_a10b["returncode"] == 0
        and final_a10f_run["returncode"] == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10H_ITERATIVE_SAFE_CLEANUP",
        "ok": ok,
        "decision": "A10H_ITERATIVE_SAFE_CLEANUP_GREEN" if ok else "A10H_ITERATIVE_SAFE_CLEANUP_NOT_GREEN",
        "quarantine_root": str(QUARANTINE_ROOT),
        "rounds": rounds,
        "moved_total": moved_total,
        "missing_total": missing_total,
        "final_safe_quarantine_candidate_count": final_safe,
        "final_cleanup_candidate_count": final_a10f.get("cleanup_candidate_count"),
        "final_keep_or_review_count": final_a10f.get("keep_or_review_count"),
        "final_by_decision": final_a10f.get("by_decision"),
        "compileall_returncode": compile_result["returncode"],
        "final_a10a_returncode": final_a10a["returncode"],
        "final_a10b_returncode": final_a10b["returncode"],
        "final_a10f_returncode": final_a10f_run["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "pytest_tail": pytest_result["combined"],
        "note": "Yalnızca A10F safe_quarantine_candidate sınıfı iteratif olarak karantinaya taşındı. Runtime, referanslı ve rename-later dosyalara dokunulmadı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10H Iterative Safe Cleanup Kararı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Quarantine root: `{result['quarantine_root']}`",
        f"- Moved total: {result['moved_total']}",
        f"- Missing total: {result['missing_total']}",
        f"- Final safe quarantine candidate count: {result['final_safe_quarantine_candidate_count']}",
        f"- Final cleanup candidate count: {result['final_cleanup_candidate_count']}",
        f"- Final keep or review count: {result['final_keep_or_review_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## Rounds",
        "",
        "```json",
        json.dumps(result["rounds"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Final A10F Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["final_by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Özeti",
        "",
        "```json",
        json.dumps(result["pytest_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        result["note"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10H_REPORT_JSON:", OUT_JSON)
    print("A10H_REPORT_MD:", OUT_MD)
    print("A10H_QUARANTINE_ROOT:", QUARANTINE_ROOT)
    print("A10H_MOVED_TOTAL:", moved_total)
    print("A10H_MISSING_TOTAL:", missing_total)
    print("A10H_FINAL_SAFE_QUARANTINE_CANDIDATE_COUNT:", final_safe)
    print("A10H_FINAL_CLEANUP_CANDIDATE_COUNT:", result["final_cleanup_candidate_count"])
    print("A10H_FINAL_KEEP_OR_REVIEW_COUNT:", result["final_keep_or_review_count"])
    print("A10H_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A10H_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A10H_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A10H_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
