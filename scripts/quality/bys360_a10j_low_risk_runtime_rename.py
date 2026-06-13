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

A10I_JSON = Path("reports/quality/BYS360_A10I_REMAINING_RUNTIME_RENAME_KEEP_PLAN.json")
OUT_JSON = Path("reports/quality/BYS360_A10J_LOW_RISK_RUNTIME_RENAME_DECISION.json")
OUT_MD = Path("reports/quality/BYS360_A10J_LOW_RISK_RUNTIME_RENAME_DECISION.md")

BACKUP_ROOT = RELEASES / f"A10J_LOW_RISK_RUNTIME_RENAME_BACKUP_{STAMP}"

TARGET_DECISION = "rename_possible_but_runtime_smoke_required"

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

def backup_and_rename(src_rel: str, dst_rel: str):
    src = ROOT / src_rel
    dst = ROOT / dst_rel
    backup = BACKUP_ROOT / src_rel

    if not src.exists():
        return {
            "source": src_rel,
            "target": dst_rel,
            "status": "source_missing",
        }

    if dst.exists():
        return {
            "source": src_rel,
            "target": dst_rel,
            "status": "target_exists_skip",
        }

    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, backup)

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

    return {
        "source": src_rel,
        "target": dst_rel,
        "backup": str(backup),
        "status": "renamed",
    }

def refresh_chain():
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

    a10i = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "scripts/quality/bys360_a10i_remaining_runtime_rename_keep_plan.py",
    ])

    return a10a, a10b, a10f, a10i

def main():
    if not A10I_JSON.exists():
        raise SystemExit("A10I raporu bulunamadı. Önce A10I çalışmalı.")

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    a10i = read_json(A10I_JSON)
    plan = a10i.get("plan", [])

    targets = [
        item for item in plan
        if item.get("a10i_decision") == TARGET_DECISION
        and item.get("suggested_new_path")
    ]

    operations = []
    for item in targets:
        src = item.get("path")
        dst = item.get("suggested_new_path")
        operations.append(backup_and_rename(src, dst))

    renamed_count = sum(1 for x in operations if x.get("status") == "renamed")
    source_missing_count = sum(1 for x in operations if x.get("status") == "source_missing")
    target_exists_count = sum(1 for x in operations if x.get("status") == "target_exists_skip")

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
    ])

    final_a10a, final_a10b, final_a10f, final_a10i_run = refresh_chain()

    refreshed_i = {}
    refreshed_i_path = Path("reports/quality/BYS360_A10I_REMAINING_RUNTIME_RENAME_KEEP_PLAN.json")
    if refreshed_i_path.exists():
        refreshed_i = read_json(refreshed_i_path)

    refreshed_f = {}
    refreshed_f_path = Path("reports/quality/BYS360_A10F_CLEANUP_CANDIDATE_PRECISION_PLAN.json")
    if refreshed_f_path.exists():
        refreshed_f = read_json(refreshed_f_path)

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

    ok = (
        len(targets) > 0
        and renamed_count == len(targets)
        and source_missing_count == 0
        and target_exists_count == 0
        and compile_result["returncode"] == 0
        and final_a10a["returncode"] == 0
        and final_a10b["returncode"] == 0
        and final_a10f["returncode"] == 0
        and final_a10i_run["returncode"] == 0
        and refreshed_f.get("safe_quarantine_candidate_count") == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10J_LOW_RISK_RUNTIME_RENAME",
        "ok": ok,
        "decision": "A10J_LOW_RISK_RUNTIME_RENAME_GREEN" if ok else "A10J_LOW_RISK_RUNTIME_RENAME_NOT_GREEN",
        "backup_root": str(BACKUP_ROOT),
        "target_count": len(targets),
        "renamed_count": renamed_count,
        "source_missing_count": source_missing_count,
        "target_exists_count": target_exists_count,
        "operations": operations,
        "compileall_returncode": compile_result["returncode"],
        "final_a10a_returncode": final_a10a["returncode"],
        "final_a10b_returncode": final_a10b["returncode"],
        "final_a10f_returncode": final_a10f["returncode"],
        "final_a10i_returncode": final_a10i_run["returncode"],
        "final_a10f_safe_quarantine_candidate_count": refreshed_f.get("safe_quarantine_candidate_count"),
        "final_a10f_cleanup_candidate_count": refreshed_f.get("cleanup_candidate_count"),
        "final_a10f_keep_or_review_count": refreshed_f.get("keep_or_review_count"),
        "final_a10i_remaining_count": refreshed_i.get("remaining_count"),
        "final_a10i_by_decision": refreshed_i.get("by_decision"),
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "pytest_tail": pytest_result["combined"],
        "note": "Yalnızca A10I düşük riskli rename_possible_but_runtime_smoke_required sınıfı yeniden adlandırıldı. Referanslı ve compatibility wrapper isteyen dosyalara dokunulmadı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10J Düşük Riskli Runtime Rename Kararı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Backup root: `{result['backup_root']}`",
        f"- Target count: {result['target_count']}",
        f"- Renamed count: {result['renamed_count']}",
        f"- Source missing count: {result['source_missing_count']}",
        f"- Target exists count: {result['target_exists_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        f"- Final A10F safe quarantine candidate count: {result['final_a10f_safe_quarantine_candidate_count']}",
        f"- Final A10F cleanup candidate count: {result['final_a10f_cleanup_candidate_count']}",
        f"- Final A10F keep or review count: {result['final_a10f_keep_or_review_count']}",
        f"- Final A10I remaining count: {result['final_a10i_remaining_count']}",
        "",
        "## Final A10I Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["final_a10i_by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Özeti",
        "",
        "```json",
        json.dumps(result["pytest_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## İşlem Listesi",
        "",
        "```json",
        json.dumps(result["operations"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        result["note"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10J_REPORT_JSON:", OUT_JSON)
    print("A10J_REPORT_MD:", OUT_MD)
    print("A10J_BACKUP_ROOT:", BACKUP_ROOT)
    print("A10J_TARGET_COUNT:", result["target_count"])
    print("A10J_RENAMED_COUNT:", result["renamed_count"])
    print("A10J_SOURCE_MISSING_COUNT:", result["source_missing_count"])
    print("A10J_TARGET_EXISTS_COUNT:", result["target_exists_count"])
    print("A10J_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A10J_FINAL_A10F_SAFE_QUARANTINE_CANDIDATE_COUNT:", result["final_a10f_safe_quarantine_candidate_count"])
    print("A10J_FINAL_A10I_REMAINING_COUNT:", result["final_a10i_remaining_count"])
    print("A10J_FINAL_A10I_BY_DECISION:", json.dumps(result["final_a10i_by_decision"], ensure_ascii=False))
    print("A10J_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A10J_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A10J_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
