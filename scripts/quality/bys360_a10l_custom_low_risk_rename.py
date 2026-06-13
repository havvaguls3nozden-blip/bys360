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

A10K_JSON = Path("reports/quality/BYS360_A10K_REMAINING_LOW_RISK_RENAME_PLAN.json")
OUT_JSON = Path("reports/quality/BYS360_A10L_CUSTOM_LOW_RISK_RENAME_DECISION.json")
OUT_MD = Path("reports/quality/BYS360_A10L_CUSTOM_LOW_RISK_RENAME_DECISION.md")

BACKUP_ROOT = RELEASES / f"A10L_CUSTOM_LOW_RISK_RENAME_BACKUP_{STAMP}"

TARGET_DECISION = "rename_with_custom_suggestion"

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

    if not src_rel or not dst_rel:
        return {
            "source": src_rel,
            "target": dst_rel,
            "status": "invalid_source_or_target",
        }

    if src_rel == dst_rel:
        return {
            "source": src_rel,
            "target": dst_rel,
            "status": "same_path_skip",
        }

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
    results = {}

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

    for key, cmd in commands.items():
        results[key] = run_cmd(cmd)

    return results

def main():
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    # A10K raporunu tazele
    a10k_initial = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "scripts/quality/bys360_a10k_remaining_low_risk_rename_plan.py",
    ])

    if not A10K_JSON.exists():
        raise SystemExit("A10K raporu bulunamadı. Önce A10K çalışmalı.")

    a10k = read_json(A10K_JSON)
    plan = a10k.get("plan", [])

    targets = [
        item for item in plan
        if item.get("a10k_decision") == TARGET_DECISION
        and item.get("custom_suggested_new_path")
        and item.get("reference_count_now", 0) == 0
    ]

    operations = []
    for item in targets:
        operations.append(
            backup_and_rename(
                item.get("path"),
                item.get("custom_suggested_new_path"),
            )
        )

    renamed_count = sum(1 for x in operations if x.get("status") == "renamed")
    source_missing_count = sum(1 for x in operations if x.get("status") == "source_missing")
    target_exists_count = sum(1 for x in operations if x.get("status") == "target_exists_skip")
    invalid_count = sum(1 for x in operations if x.get("status") == "invalid_source_or_target")
    same_path_count = sum(1 for x in operations if x.get("status") == "same_path_skip")

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
    ])

    refreshed = refresh_chain()

    refreshed_f = {}
    f_path = Path("reports/quality/BYS360_A10F_CLEANUP_CANDIDATE_PRECISION_PLAN.json")
    if f_path.exists():
        refreshed_f = read_json(f_path)

    refreshed_i = {}
    i_path = Path("reports/quality/BYS360_A10I_REMAINING_RUNTIME_RENAME_KEEP_PLAN.json")
    if i_path.exists():
        refreshed_i = read_json(i_path)

    refreshed_k = {}
    k_path = Path("reports/quality/BYS360_A10K_REMAINING_LOW_RISK_RENAME_PLAN.json")
    if k_path.exists():
        refreshed_k = read_json(k_path)

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
        a10k_initial["returncode"] == 0
        and renamed_count == len(targets)
        and source_missing_count == 0
        and target_exists_count == 0
        and invalid_count == 0
        and same_path_count == 0
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
        "phase": "A10L_CUSTOM_LOW_RISK_RENAME",
        "ok": ok,
        "decision": "A10L_CUSTOM_LOW_RISK_RENAME_GREEN" if ok else "A10L_CUSTOM_LOW_RISK_RENAME_NOT_GREEN",
        "backup_root": str(BACKUP_ROOT),
        "initial_a10k_returncode": a10k_initial["returncode"],
        "target_count": len(targets),
        "renamed_count": renamed_count,
        "source_missing_count": source_missing_count,
        "target_exists_count": target_exists_count,
        "invalid_count": invalid_count,
        "same_path_count": same_path_count,
        "operations": operations,
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
        "note": "A10K custom suggestion üreten düşük riskli dosyalar yedekli yeniden adlandırıldı. Keep allowlist adaylarına ve referanslı dosyalara dokunulmadı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10L Custom Low Risk Rename Kararı",
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
        f"- Invalid count: {result['invalid_count']}",
        f"- Same path count: {result['same_path_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        f"- Final A10F safe quarantine candidate count: {result['final_a10f_safe_quarantine_candidate_count']}",
        f"- Final A10F cleanup candidate count: {result['final_a10f_cleanup_candidate_count']}",
        f"- Final A10I remaining count: {result['final_a10i_remaining_count']}",
        f"- Final A10K remaining low risk count: {result['final_a10k_remaining_low_risk_count']}",
        "",
        "## Refresh Returncodes",
        "",
        "```json",
        json.dumps(result["refresh_returncodes"], ensure_ascii=False, indent=2),
        "```",
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
        "## İşlemler",
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

    print("A10L_REPORT_JSON:", OUT_JSON)
    print("A10L_REPORT_MD:", OUT_MD)
    print("A10L_BACKUP_ROOT:", BACKUP_ROOT)
    print("A10L_TARGET_COUNT:", result["target_count"])
    print("A10L_RENAMED_COUNT:", result["renamed_count"])
    print("A10L_SOURCE_MISSING_COUNT:", result["source_missing_count"])
    print("A10L_TARGET_EXISTS_COUNT:", result["target_exists_count"])
    print("A10L_INVALID_COUNT:", result["invalid_count"])
    print("A10L_SAME_PATH_COUNT:", result["same_path_count"])
    print("A10L_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A10L_FINAL_A10F_SAFE_QUARANTINE_CANDIDATE_COUNT:", result["final_a10f_safe_quarantine_candidate_count"])
    print("A10L_FINAL_A10I_REMAINING_COUNT:", result["final_a10i_remaining_count"])
    print("A10L_FINAL_A10I_BY_DECISION:", json.dumps(result["final_a10i_by_decision"], ensure_ascii=False))
    print("A10L_FINAL_A10K_REMAINING_LOW_RISK_COUNT:", result["final_a10k_remaining_low_risk_count"])
    print("A10L_FINAL_A10K_BY_DECISION:", json.dumps(result["final_a10k_by_decision"], ensure_ascii=False))
    print("A10L_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A10L_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A10L_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
