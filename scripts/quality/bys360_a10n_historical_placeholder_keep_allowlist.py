from pathlib import Path
from datetime import datetime
import json
import subprocess
import os
import re

ROOT = Path(".").resolve()

A10M_JSON = Path("reports/quality/BYS360_A10M_PLACEHOLDER_RENAME_FIX_DECISION.json")
A10F_JSON = Path("reports/quality/BYS360_A10F_CLEANUP_CANDIDATE_PRECISION_PLAN.json")
A10I_JSON = Path("reports/quality/BYS360_A10I_REMAINING_RUNTIME_RENAME_KEEP_PLAN.json")
A10K_JSON = Path("reports/quality/BYS360_A10K_REMAINING_LOW_RISK_RENAME_PLAN.json")

OUT_JSON = Path("reports/quality/BYS360_A10N_HISTORICAL_PLACEHOLDER_KEEP_ALLOWLIST_DECISION.json")
OUT_MD = Path("reports/quality/BYS360_A10N_HISTORICAL_PLACEHOLDER_KEEP_ALLOWLIST_DECISION.md")

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

def is_historical_placeholder(row):
    path = row.get("path") or row.get("source") or ""
    return (
        path.startswith("migrations/versions/")
        and path.endswith("_historical_placeholder.py")
    )

def main():
    if not A10M_JSON.exists():
        raise SystemExit("A10M raporu bulunamadı. Önce A10M çalışmalı.")

    a10m = read_json(A10M_JSON)

    # Zinciri tazele
    refresh = {
        "a10a": run_cmd([
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "scripts/quality/bys360_a10a_phase_dev_debug_audit.py",
        ]),
        "a10b": run_cmd([
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "scripts/quality/bys360_a10b_phase_dev_debug_precision_audit.py",
        ]),
        "a10f": run_cmd([
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "scripts/quality/bys360_a10f_cleanup_candidate_precision_plan.py",
        ]),
        "a10i": run_cmd([
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "scripts/quality/bys360_a10i_remaining_runtime_rename_keep_plan.py",
        ]),
        "a10k": run_cmd([
            str(ROOT / ".venv" / "Scripts" / "python.exe"),
            "scripts/quality/bys360_a10k_remaining_low_risk_rename_plan.py",
        ]),
    }

    a10f = read_json(A10F_JSON) if A10F_JSON.exists() else {}
    a10i = read_json(A10I_JSON) if A10I_JSON.exists() else {}
    a10k = read_json(A10K_JSON) if A10K_JSON.exists() else {}

    low_risk_plan = a10k.get("plan", [])
    historical_placeholder_keep = [row for row in low_risk_plan if is_historical_placeholder(row)]
    non_placeholder_low_risk = [row for row in low_risk_plan if not is_historical_placeholder(row)]

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
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
    refresh_ok = all(item["returncode"] == 0 for item in refresh.values())

    ok = (
        a10m.get("ok") is True
        and refresh_ok
        and compile_result["returncode"] == 0
        and a10f.get("safe_quarantine_candidate_count") == 0
        and len(historical_placeholder_keep) == 7
        and len(non_placeholder_low_risk) == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10N_HISTORICAL_PLACEHOLDER_KEEP_ALLOWLIST",
        "ok": ok,
        "decision": "A10N_HISTORICAL_PLACEHOLDER_KEEP_ALLOWLIST_GREEN" if ok else "A10N_HISTORICAL_PLACEHOLDER_KEEP_ALLOWLIST_NOT_GREEN",
        "a10m_ok": a10m.get("ok"),
        "refresh_returncodes": {k: v["returncode"] for k, v in refresh.items()},
        "compileall_returncode": compile_result["returncode"],
        "a10f_safe_quarantine_candidate_count": a10f.get("safe_quarantine_candidate_count"),
        "a10f_cleanup_candidate_count": a10f.get("cleanup_candidate_count"),
        "a10f_keep_or_review_count": a10f.get("keep_or_review_count"),
        "a10i_remaining_count": a10i.get("remaining_count"),
        "a10i_by_decision": a10i.get("by_decision"),
        "a10k_remaining_low_risk_count": a10k.get("remaining_low_risk_count"),
        "a10k_by_decision": a10k.get("by_decision"),
        "historical_placeholder_keep_count": len(historical_placeholder_keep),
        "historical_placeholder_keep": historical_placeholder_keep,
        "non_placeholder_low_risk_count": len(non_placeholder_low_risk),
        "non_placeholder_low_risk": non_placeholder_low_risk,
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "pytest_tail": pytest_result["combined"],
        "note": "historical_placeholder migration dosyaları Alembic tarihsel uyumluluk dosyasıdır. Placeholder içindeki 'old' harf dizisi false-positive kabul edilerek rename edilmeyecek ve keep allowlist kapsamında korunacaktır.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10N Historical Placeholder Keep Allowlist Kararı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- A10M OK: {result['a10m_ok']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        f"- A10F safe quarantine candidate count: {result['a10f_safe_quarantine_candidate_count']}",
        f"- A10F cleanup candidate count: {result['a10f_cleanup_candidate_count']}",
        f"- A10I remaining count: {result['a10i_remaining_count']}",
        f"- A10K remaining low risk count: {result['a10k_remaining_low_risk_count']}",
        f"- Historical placeholder keep count: {result['historical_placeholder_keep_count']}",
        f"- Non-placeholder low risk count: {result['non_placeholder_low_risk_count']}",
        "",
        "## Refresh Returncodes",
        "",
        "```json",
        json.dumps(result["refresh_returncodes"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## A10I Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["a10i_by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## A10K Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["a10k_by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Historical Placeholder Keep List",
        "",
        "```json",
        json.dumps(result["historical_placeholder_keep"], ensure_ascii=False, indent=2),
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

    print("A10N_REPORT_JSON:", OUT_JSON)
    print("A10N_REPORT_MD:", OUT_MD)
    print("A10N_A10M_OK:", result["a10m_ok"])
    print("A10N_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A10N_A10F_SAFE_QUARANTINE_CANDIDATE_COUNT:", result["a10f_safe_quarantine_candidate_count"])
    print("A10N_A10F_CLEANUP_CANDIDATE_COUNT:", result["a10f_cleanup_candidate_count"])
    print("A10N_A10I_REMAINING_COUNT:", result["a10i_remaining_count"])
    print("A10N_A10K_REMAINING_LOW_RISK_COUNT:", result["a10k_remaining_low_risk_count"])
    print("A10N_HISTORICAL_PLACEHOLDER_KEEP_COUNT:", result["historical_placeholder_keep_count"])
    print("A10N_NON_PLACEHOLDER_LOW_RISK_COUNT:", result["non_placeholder_low_risk_count"])
    print("A10N_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A10N_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A10N_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
