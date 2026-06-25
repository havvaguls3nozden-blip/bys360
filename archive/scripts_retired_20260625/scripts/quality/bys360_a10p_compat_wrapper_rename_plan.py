from pathlib import Path
from datetime import datetime
import json
import subprocess
import os
import re

ROOT = Path(".").resolve()

A10O_JSON = Path("reports/quality/BYS360_A10O_FINAL_KEEP_COMPAT_PLAN.json")
OUT_JSON = Path("reports/quality/BYS360_A10P_COMPAT_WRAPPER_RENAME_PLAN.json")
OUT_MD = Path("reports/quality/BYS360_A10P_COMPAT_WRAPPER_RENAME_PLAN.md")

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

def classify_compat(row):
    path = row.get("path", "")
    suffix = row.get("suffix", "")
    suggested = row.get("suggested_new_path")
    refs = row.get("references_now_sample") or row.get("references_sample") or []

    low = path.lower()

    if ".disabled_by_" in low or "disabled" in low:
        return {
            "a10p_decision": "keep_allowlist_archived_disabled_asset",
            "apply_allowed": False,
            "reason": "Devre dışı bırakılmış/arsiv nitelikli dosya; referanslar kalite/restore scriptlerinden geliyor. Rename yapmak yerine keep allowlist daha güvenli.",
        }

    if path.startswith("app/static/"):
        return {
            "a10p_decision": "keep_allowlist_referenced_static_asset",
            "apply_allowed": False,
            "reason": "Static CSS/JS dosyası referanslı asset olarak görünüyor. Cache/template/rollback bağı olabileceği için rename yerine keep allowlist daha güvenli.",
        }

    if suffix == ".py" and path.startswith("app/") and suggested:
        return {
            "a10p_decision": "python_compat_wrapper_candidate",
            "apply_allowed": True,
            "reason": "Python runtime dosyası. Yeni ad oluşturulabilir; eski path için compatibility wrapper bırakılarak import kırılması önlenebilir.",
        }

    if suffix == ".py" and suggested:
        return {
            "a10p_decision": "python_reference_update_candidate",
            "apply_allowed": False,
            "reason": "Python dosyası ama app runtime dışında veya özel referanslı. Önce manuel import/update planı gerekir.",
        }

    return {
        "a10p_decision": "keep_allowlist_manual_reason_required",
        "apply_allowed": False,
        "reason": "Güvenli otomatik wrapper/rename için yeterli koşul oluşmadı. Keep allowlist veya manuel karar gerekir.",
    }

def main():
    if not A10O_JSON.exists():
        raise SystemExit("A10O raporu bulunamadı. Önce A10O çalışmalı.")

    a10o = read_json(A10O_JSON)
    compat_required = a10o.get("compat_required", [])

    plan = []
    by_decision = {}

    for row in compat_required:
        decision = classify_compat(row)

        item = dict(row)
        item.update(decision)
        item["old_path"] = row.get("path")
        item["new_path"] = row.get("suggested_new_path")
        item["reference_count_now"] = row.get("reference_count_now")
        item["references_now_sample"] = row.get("references_now_sample", [])[:20]

        plan.append(item)
        by_decision[item["a10p_decision"]] = by_decision.get(item["a10p_decision"], 0) + 1

    apply_candidates = [x for x in plan if x.get("apply_allowed")]
    keep_allowlist = [x for x in plan if not x.get("apply_allowed")]

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

    ok = (
        a10o.get("ok") is True
        and len(compat_required) == 7
        and len(plan) == 7
        and compile_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10P_COMPAT_WRAPPER_RENAME_PLAN",
        "mode": "plan_only",
        "ok": ok,
        "decision": "A10P_COMPAT_WRAPPER_RENAME_PLAN_GREEN" if ok else "A10P_COMPAT_WRAPPER_RENAME_PLAN_NOT_GREEN",
        "a10o_ok": a10o.get("ok"),
        "compat_required_count": len(compat_required),
        "by_decision": by_decision,
        "apply_candidate_count": len(apply_candidates),
        "apply_candidates": apply_candidates,
        "keep_allowlist_count": len(keep_allowlist),
        "keep_allowlist": keep_allowlist,
        "plan": plan,
        "compileall_returncode": compile_result["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "pytest_tail": pytest_result["combined"],
        "next_action": "A10Q: apply_candidates listesindeki Python dosyaları için yedekli rename + eski path wrapper uygulanabilir. Keep allowlist dosyaları rename edilmeyecek.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10P Compat Wrapper Rename Plan",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- A10O OK: {result['a10o_ok']}",
        f"- Compat required count: {result['compat_required_count']}",
        f"- Apply candidate count: {result['apply_candidate_count']}",
        f"- Keep allowlist count: {result['keep_allowlist_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Apply Candidates",
        "",
        "```json",
        json.dumps(result["apply_candidates"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Keep Allowlist",
        "",
        "```json",
        json.dumps(result["keep_allowlist"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Özeti",
        "",
        "```json",
        json.dumps(result["pytest_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10P_REPORT_JSON:", OUT_JSON)
    print("A10P_REPORT_MD:", OUT_MD)
    print("A10P_A10O_OK:", result["a10o_ok"])
    print("A10P_COMPAT_REQUIRED_COUNT:", result["compat_required_count"])
    print("A10P_BY_DECISION:", json.dumps(result["by_decision"], ensure_ascii=False))
    print("A10P_APPLY_CANDIDATE_COUNT:", result["apply_candidate_count"])
    print("A10P_KEEP_ALLOWLIST_COUNT:", result["keep_allowlist_count"])
    print("A10P_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A10P_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A10P_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A10P_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
