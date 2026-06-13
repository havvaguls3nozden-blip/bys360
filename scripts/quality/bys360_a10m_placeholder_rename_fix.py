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

A10L_JSON = Path("reports/quality/BYS360_A10L_CUSTOM_LOW_RISK_RENAME_DECISION.json")
OUT_JSON = Path("reports/quality/BYS360_A10M_PLACEHOLDER_RENAME_FIX_DECISION.json")
OUT_MD = Path("reports/quality/BYS360_A10M_PLACEHOLDER_RENAME_FIX_DECISION.md")

BACKUP_ROOT = RELEASES / f"A10M_PLACEHOLDER_RENAME_FIX_BACKUP_{STAMP}"

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

def restore_bad_placeholder_name(operation):
    source_rel = operation.get("source")
    target_rel = operation.get("target")

    if not source_rel or not target_rel:
        return {
            "source": source_rel,
            "target": target_rel,
            "status": "invalid_operation",
        }

    if "historical_placeholder.py" not in source_rel:
        return {
            "source": source_rel,
            "target": target_rel,
            "status": "not_placeholder_skip",
        }

    if "placeharchiveer.py" not in target_rel:
        return {
            "source": source_rel,
            "target": target_rel,
            "status": "not_bad_target_skip",
        }

    src_original = ROOT / source_rel
    bad_target = ROOT / target_rel
    backup_bad = BACKUP_ROOT / target_rel

    if src_original.exists():
        return {
            "source": source_rel,
            "target": target_rel,
            "status": "original_already_exists_skip",
        }

    if not bad_target.exists():
        return {
            "source": source_rel,
            "target": target_rel,
            "status": "bad_target_missing",
        }

    backup_bad.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bad_target, backup_bad)

    src_original.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(bad_target), str(src_original))

    return {
        "source": source_rel,
        "target": target_rel,
        "backup_bad_target": str(backup_bad),
        "status": "restored_to_original_placeholder_name",
    }

def refresh_chain():
    commands = {
        "a10a": [
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "scripts/quality/bys360_a10a_phase_dev_debug_audit.py",
        ],
        "a10b": [
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "scripts/quality/bys360_a10b_phase_dev_debug_precision_audit.py",
        ],
        "a10f": [
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "scripts/quality/bys360_a10f_cleanup_candidate_precision_plan.py",
        ],
        "a10i": [
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "scripts/quality/bys360_a10i_remaining_runtime_rename_keep_plan.py",
        ],
        "a10k": [
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "scripts/quality/bys360_a10k_remaining_low_risk_rename_plan.py",
        ],
    }

    return {key: run_cmd(cmd) for key, cmd in commands.items()}

def main():
    if not A10L_JSON.exists():
        raise SystemExit("A10L raporu bulunamadı. Önce A10L çalışmalı.")

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    a10l = read_json(A10L_JSON)
    operations = a10l.get("operations", [])

    fixes = []
    for op in operations:
        fixes.append(restore_bad_placeholder_name(op))

    restored_count = sum(1 for x in fixes if x.get("status") == "restored_to_original_placeholder_name")
    bad_missing_count = sum(1 for x in fixes if x.get("status") == "bad_target_missing")
    invalid_count = sum(1 for x in fixes if x.get("status") == "invalid_operation")

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
    ])

    refreshed = refresh_chain()

    f_path = Path("reports/quality/BYS360_A10F_CLEANUP_CANDIDATE_PRECISION_PLAN.json")
    i_path = Path("reports/quality/BYS360_A10I_REMAINING_RUNTIME_RENAME_KEEP_PLAN.json")
    k_path = Path("reports/quality/BYS360_A10K_REMAINING_LOW_RISK_RENAME_PLAN.json")

    refreshed_f = read_json(f_path) if f_path.exists() else {}
    refreshed_i = read_json(i_path) if i_path.exists() else {}
    refreshed_k = read_json(k_path) if k_path.exists() else {}

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

    command_ok = all(x["returncode"] == 0 for x in refreshed.values())

    ok = (
        restored_count == 7
        and bad_missing_count == 0
        and invalid_count == 0
        and compile_result["returncode"] == 0
        and command_ok
        and refreshed_f.get("safe_quarantine_candidate_count") == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10M_PLACEHOLDER_RENAME_FIX",
        "ok": ok,
        "decision": "A10M_PLACEHOLDER_RENAME_FIX_GREEN" if ok else "A10M_PLACEHOLDER_RENAME_FIX_NOT_GREEN",
        "backup_root": str(BACKUP_ROOT),
        "restored_count": restored_count,
        "bad_missing_count": bad_missing_count,
        "invalid_count": invalid_count,
        "fixes": fixes,
        "compileall_returncode": compile_result["returncode"],
        "refresh_returncodes": {k: v["returncode"] for k, v in refreshed.items()},
        "final_a10f_safe_quarantine_candidate_count": refreshed_f.get("safe_quarantine_candidate_count"),
        "final_a10f_cleanup_candidate_count": refreshed_f.get("cleanup_candidate_count"),
        "final_a10f_keep_or_review_count": refreshed_f.get("keep_or_review_count"),
        "final_a10i_remaining_count": refreshed_i.get("remaining_count"),
        "final_a10i_by_decision": refreshed_i.get("by_decision"),
        "final_a10k_remaining_low_risk_count": refreshed_k.get("remaining_low_risk_count"),
        "final_a10k_by_decision": refreshed_k.get("by_decision"),
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "pytest_tail": pytest_result["combined"],
        "note": "A10L sonrasında oluşan placeharchiveer dosya adları kalite nedeniyle orijinal historical_placeholder adına geri alındı. Bu dosyalar Alembic tarihsel placeholder olarak korunacaktır.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10M Placeholder Rename Fix Kararı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Backup root: `{result['backup_root']}`",
        f"- Restored count: {result['restored_count']}",
        f"- Bad missing count: {result['bad_missing_count']}",
        f"- Invalid count: {result['invalid_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        f"- Final A10F safe quarantine candidate count: {result['final_a10f_safe_quarantine_candidate_count']}",
        f"- Final A10F cleanup candidate count: {result['final_a10f_cleanup_candidate_count']}",
        f"- Final A10I remaining count: {result['final_a10i_remaining_count']}",
        f"- Final A10K remaining low risk count: {result['final_a10k_remaining_low_risk_count']}",
        "",
        "## Final A10I Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["final_a10i_by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Final A10K Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["final_a10k_by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Özeti",
        "",
        "```json",
        json.dumps(result["pytest_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Düzeltmeler",
        "",
        "```json",
        json.dumps(result["fixes"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        result["note"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10M_REPORT_JSON:", OUT_JSON)
    print("A10M_REPORT_MD:", OUT_MD)
    print("A10M_BACKUP_ROOT:", BACKUP_ROOT)
    print("A10M_RESTORED_COUNT:", result["restored_count"])
    print("A10M_BAD_MISSING_COUNT:", result["bad_missing_count"])
    print("A10M_INVALID_COUNT:", result["invalid_count"])
    print("A10M_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A10M_FINAL_A10F_SAFE_QUARANTINE_CANDIDATE_COUNT:", result["final_a10f_safe_quarantine_candidate_count"])
    print("A10M_FINAL_A10I_REMAINING_COUNT:", result["final_a10i_remaining_count"])
    print("A10M_FINAL_A10I_BY_DECISION:", json.dumps(result["final_a10i_by_decision"], ensure_ascii=False))
    print("A10M_FINAL_A10K_REMAINING_LOW_RISK_COUNT:", result["final_a10k_remaining_low_risk_count"])
    print("A10M_FINAL_A10K_BY_DECISION:", json.dumps(result["final_a10k_by_decision"], ensure_ascii=False))
    print("A10M_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A10M_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A10M_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
