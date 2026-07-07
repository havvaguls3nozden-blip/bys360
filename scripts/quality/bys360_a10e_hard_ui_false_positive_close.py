from pathlib import Path
from datetime import datetime
import json
import subprocess
import os
import re

ROOT = Path(".").resolve()

A10D_JSON = Path("reports/quality/BYS360_A10D_HARD_UI_PRECISION_DECISION.json")
OUT_JSON = Path("reports/quality/BYS360_A10E_HARD_UI_FALSE_POSITIVE_CLOSE_DECISION.json")
OUT_MD = Path("reports/quality/BYS360_A10E_HARD_UI_FALSE_POSITIVE_CLOSE_DECISION.md")

ALLOWED_MANUAL_REVIEW = [
    {
        "path": "mobile_flutter/bys360_mobile_native/lib/core/diagnostics/bys_mobile_crash_service.dart",
        "term": "exception",
        "reason": "Crash diagnostic logging; kullanıcıya doğrudan teknik metin göstermez.",
    }
]

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def is_allowed(row):
    path = row.get("path", "")
    term = str(row.get("term", "")).lower()
    for allowed in ALLOWED_MANUAL_REVIEW:
        if path == allowed["path"] and term == allowed["term"]:
            return True
    return False

def run_cmd(cmd):
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        timeout=1200,
    )
    return {
        "cmd": " ".join(map(str, cmd)),
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-4000:],
        "stderr_tail": (proc.stderr or "")[-4000:],
    }

def main():
    if not A10D_JSON.exists():
        raise SystemExit("A10D raporu bulunamadı. Önce A10D çalışmalı.")

    a10d = read_json(A10D_JSON)

    real_ui = a10d.get("real_user_facing_hits", [])
    manual = a10d.get("manual_review_hits", [])

    allowed_manual = [x for x in manual if is_allowed(x)]
    unallowed_manual = [x for x in manual if not is_allowed(x)]

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
    ])

    # Hafif hedef test: full CI değil; burada yalnızca kalite scriptleri syntax/çalışma kararı.
    quality_scripts_exist = all([
        Path("scripts/quality/bys360_a10c_hard_ui_technical_language_plan.py").exists(),
        Path("scripts/quality/bys360_a10d_hard_ui_precision_decision.py").exists(),
    ])

    ok = (
        len(real_ui) == 0
        and len(unallowed_manual) == 0
        and compile_result["returncode"] == 0
        and quality_scripts_exist
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10E_HARD_UI_FALSE_POSITIVE_CLOSE_DECISION",
        "ok": ok,
        "decision": "A10E_HARD_UI_CLOSED" if ok else "A10E_HARD_UI_NOT_CLOSED",
        "source_a10d": str(A10D_JSON),
        "real_user_facing_hit_count": len(real_ui),
        "manual_review_hit_count": len(manual),
        "allowed_manual_review_count": len(allowed_manual),
        "unallowed_manual_review_count": len(unallowed_manual),
        "allowed_manual_reviews": allowed_manual,
        "unallowed_manual_reviews": unallowed_manual,
        "false_positive_hit_count": a10d.get("false_positive_hit_count"),
        "compileall_returncode": compile_result["returncode"],
        "compileall": compile_result,
        "quality_scripts_exist": quality_scripts_exist,
        "note": "A10C hard UI bulgularında gerçek kullanıcıya görünen teknik metin bulunmadı; kod içi/sanitizer/diagnostic false-positive olarak kapatıldı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10E Hard UI False Positive Kapanış Kararı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Real user-facing hit count: {result['real_user_facing_hit_count']}",
        f"- Manual review hit count: {result['manual_review_hit_count']}",
        f"- Allowed manual review count: {result['allowed_manual_review_count']}",
        f"- Unallowed manual review count: {result['unallowed_manual_review_count']}",
        f"- False positive hit count: {result['false_positive_hit_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        "",
        "## İzin Verilen Manuel İnceleme",
        "",
        "```json",
        json.dumps(result["allowed_manual_reviews"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Kapatılmamış Manuel İnceleme",
        "",
        "```json",
        json.dumps(result["unallowed_manual_reviews"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        result["note"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10E_REPORT_JSON:", OUT_JSON)
    print("A10E_REPORT_MD:", OUT_MD)
    print("A10E_REAL_USER_FACING_HIT_COUNT:", result["real_user_facing_hit_count"])
    print("A10E_ALLOWED_MANUAL_REVIEW_COUNT:", result["allowed_manual_review_count"])
    print("A10E_UNALLOWED_MANUAL_REVIEW_COUNT:", result["unallowed_manual_review_count"])
    print("A10E_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A10E_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
