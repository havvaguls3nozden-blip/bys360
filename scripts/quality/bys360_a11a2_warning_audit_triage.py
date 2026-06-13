from pathlib import Path
from datetime import datetime
import json
import subprocess
import os
import re

ROOT = Path(".").resolve()

OUT_JSON = Path("reports/quality/BYS360_A11A2_WARNING_AUDIT_TRIAGE.json")
OUT_MD = Path("reports/quality/BYS360_A11A2_WARNING_AUDIT_TRIAGE.md")
BASELINE_RAW = Path("reports/quality/BYS360_A11A2_BASELINE_PYTEST_RAW.txt")
WARNING_RAW = Path("reports/quality/BYS360_A11A2_WARNING_MODE_PYTEST_RAW.txt")

def run_cmd(cmd, *, warning_mode=False, timeout=1800):
    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
    }

    if warning_mode:
        env["PYTHONWARNINGS"] = "default"

    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
        env=env,
        timeout=timeout,
    )

    return {
        "cmd": " ".join(map(str, cmd)),
        "returncode": proc.returncode,
        "stdout": proc.stdout or "",
        "stderr": proc.stderr or "",
        "combined": (proc.stdout or "") + "\n" + (proc.stderr or ""),
    }

def parse_pytest_summary(text: str):
    summary = {}

    # Normal pytest short summary: "744 passed, 2 skipped, 34 deselected, 32 warnings in ..."
    for num, key in re.findall(r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warnings|warning)", text or ""):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)

    return summary

def extract_diagnostics(text: str, limit=160):
    patterns = [
        "ERROR",
        "FAILED",
        "Traceback",
        "ImportError",
        "ModuleNotFoundError",
        "SyntaxError",
        "INTERNALERROR",
        "no tests ran",
        "collected 0",
        "KeyboardInterrupt",
        "Timeout",
    ]

    hits = []
    lines = text.splitlines()

    for i, line in enumerate(lines):
        low = line.lower()
        if any(p.lower() in low for p in patterns):
            hits.append({
                "line_index": i,
                "line": line,
                "context": "\n".join(lines[max(0, i-3): min(len(lines), i+5)]),
            })

    return hits[:limit]

def tail(text: str, n=220):
    return "\n".join(text.splitlines()[-n:])

def main():
    pytest_cmd = [
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ]

    baseline = run_cmd(pytest_cmd, warning_mode=False)
    warning_mode = run_cmd(pytest_cmd, warning_mode=True)

    BASELINE_RAW.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_RAW.write_text(baseline["combined"], encoding="utf-8")
    WARNING_RAW.write_text(warning_mode["combined"], encoding="utf-8")

    baseline_summary = parse_pytest_summary(baseline["combined"])
    warning_summary = parse_pytest_summary(warning_mode["combined"])

    baseline_diag = extract_diagnostics(baseline["combined"])
    warning_diag = extract_diagnostics(warning_mode["combined"])

    if baseline["returncode"] == 0 and warning_mode["returncode"] != 0:
        diagnosis = "warning_mode_or_audit_env_issue"
        next_action = "Normal pytest yeşil, warning-mode kırılıyor. A11A audit metodu yumuşatılmalı; kod düzeltmeye geçmeden warning çıktısı farklı yöntemle alınmalı."
    elif baseline["returncode"] != 0:
        diagnosis = "baseline_pytest_failure"
        next_action = "Önce normal pytest failure/import/collection hatası çözülmeli; A11 Warning Zero'ya geçilmemeli."
    elif baseline["returncode"] == 0 and warning_mode["returncode"] == 0:
        diagnosis = "both_green"
        next_action = "A11A parser iyileştirilip warning family yeniden çıkarılabilir."
    else:
        diagnosis = "manual_review"
        next_action = "Ham pytest çıktısı manuel incelenmeli."

    ok = baseline["returncode"] == 0

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A11A2_WARNING_AUDIT_TRIAGE",
        "mode": "diagnostic_only",
        "ok": ok,
        "diagnosis": diagnosis,
        "baseline_returncode": baseline["returncode"],
        "baseline_summary": baseline_summary,
        "baseline_raw": str(BASELINE_RAW),
        "baseline_diagnostics": baseline_diag,
        "warning_mode_returncode": warning_mode["returncode"],
        "warning_mode_summary": warning_summary,
        "warning_mode_raw": str(WARNING_RAW),
        "warning_mode_diagnostics": warning_diag,
        "next_action": next_action,
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A11A2 Warning Audit Triage",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Diagnosis: {diagnosis}",
        f"- Baseline returncode: {result['baseline_returncode']}",
        f"- Warning mode returncode: {result['warning_mode_returncode']}",
        "",
        "## Baseline Pytest Summary",
        "",
        "```json",
        json.dumps(result["baseline_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Warning Mode Pytest Summary",
        "",
        "```json",
        json.dumps(result["warning_mode_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Baseline Diagnostics",
        "",
        "```json",
        json.dumps(result["baseline_diagnostics"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Warning Mode Diagnostics",
        "",
        "```json",
        json.dumps(result["warning_mode_diagnostics"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Warning Mode Tail",
        "",
        "```text",
        tail(warning_mode["combined"]),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A11A2_REPORT_JSON:", OUT_JSON)
    print("A11A2_REPORT_MD:", OUT_MD)
    print("A11A2_BASELINE_RAW:", BASELINE_RAW)
    print("A11A2_WARNING_RAW:", WARNING_RAW)
    print("A11A2_BASELINE_RETURN_CODE:", result["baseline_returncode"])
    print("A11A2_BASELINE_SUMMARY:", json.dumps(result["baseline_summary"], ensure_ascii=False))
    print("A11A2_WARNING_MODE_RETURN_CODE:", result["warning_mode_returncode"])
    print("A11A2_WARNING_MODE_SUMMARY:", json.dumps(result["warning_mode_summary"], ensure_ascii=False))
    print("A11A2_DIAGNOSIS:", diagnosis)
    print("A11A2_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
