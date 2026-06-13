from pathlib import Path
from datetime import datetime
import json
import subprocess
import os
import re
import zipfile
import hashlib

ROOT = Path(".").resolve()
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

OUT_JSON = Path("reports/quality/BYS360_A10R_FINAL_TECH_DEBT_EVIDENCE.json")
OUT_MD = Path("reports/quality/BYS360_A10R_FINAL_TECH_DEBT_EVIDENCE.md")
OUT_ZIP = RELEASES / f"BYS360_A10R_FINAL_TECH_DEBT_EVIDENCE_{STAMP}.zip"

A10N_JSON = Path("reports/quality/BYS360_A10N_HISTORICAL_PLACEHOLDER_KEEP_ALLOWLIST_DECISION.json")
A10O_JSON = Path("reports/quality/BYS360_A10O_FINAL_KEEP_COMPAT_PLAN.json")
A10P_JSON = Path("reports/quality/BYS360_A10P_COMPAT_WRAPPER_RENAME_PLAN.json")
A10Q_JSON = Path("reports/quality/BYS360_A10Q_COMPAT_WRAPPER_RENAME_APPLY_DECISION.json")

WRAPPER_MARKER = "A10Q_COMPATIBILITY_WRAPPER"

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def rel(path: Path):
    return str(path.resolve().relative_to(ROOT)).replace("\\", "/")

def run_cmd(cmd, timeout=1800):
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
        "combined": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-15000:],
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

def module_name_from_path(rel_path: str):
    if not rel_path or not rel_path.endswith(".py"):
        return None
    return rel_path[:-3].replace("/", ".").replace("\\", ".")

def verify_wrappers(a10q):
    checks = []
    for op in a10q.get("operations", []):
        old_rel = op.get("old_path")
        new_rel = op.get("new_path")

        old_path = ROOT / old_rel
        new_path = ROOT / new_rel

        old_exists = old_path.exists()
        new_exists = new_path.exists()

        wrapper_has_marker = False
        wrapper_mentions_new = False

        if old_exists:
            text = old_path.read_text(encoding="utf-8-sig", errors="ignore")
            wrapper_has_marker = WRAPPER_MARKER in text
            wrapper_mentions_new = Path(new_rel).stem in text

        status = (
            "ok"
            if old_exists and new_exists and wrapper_has_marker and wrapper_mentions_new
            else "not_ok"
        )

        checks.append({
            "old_path": old_rel,
            "new_path": new_rel,
            "old_exists": old_exists,
            "new_exists": new_exists,
            "wrapper_has_marker": wrapper_has_marker,
            "wrapper_mentions_new_module": wrapper_mentions_new,
            "status": status,
        })

    return checks

def make_import_smoke(a10q):
    modules = []

    for op in a10q.get("operations", []):
        old_mod = module_name_from_path(op.get("old_path"))
        new_mod = module_name_from_path(op.get("new_path"))
        if old_mod:
            modules.append(old_mod)
        if new_mod:
            modules.append(new_mod)

    modules = sorted(set(modules))

    code = (
        "import importlib\n"
        f"mods = {modules!r}\n"
        "for m in mods:\n"
        "    importlib.import_module(m)\n"
        "print('A10R_IMPORT_SMOKE_OK')\n"
    )

    return run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-c",
        code,
    ])

def collect_evidence_files():
    files = []

    for path in Path("reports/quality").glob("BYS360_A10*.json"):
        files.append(path)

    for path in Path("reports/quality").glob("BYS360_A10*.md"):
        files.append(path)

    for path in Path("scripts/quality").glob("bys360_a10*.py"):
        files.append(path)

    extra = [
        A10N_JSON,
        A10O_JSON,
        A10P_JSON,
        A10Q_JSON,
        OUT_JSON,
        OUT_MD,
    ]

    for path in extra:
        if path.exists():
            files.append(path)

    unique = []
    seen = set()
    for path in files:
        if path.exists():
            key = rel(path)
            if key not in seen:
                seen.add(key)
                unique.append(path)

    return unique

def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    missing = [
        str(path) for path in [A10N_JSON, A10O_JSON, A10P_JSON, A10Q_JSON]
        if not path.exists()
    ]
    if missing:
        raise SystemExit("Eksik A10 raporu var: " + ", ".join(missing))

    RELEASES.mkdir(parents=True, exist_ok=True)

    a10n = read_json(A10N_JSON)
    a10o = read_json(A10O_JSON)
    a10p = read_json(A10P_JSON)
    a10q = read_json(A10Q_JSON)

    wrapper_checks = verify_wrappers(a10q)
    wrapper_not_ok_count = sum(1 for row in wrapper_checks if row["status"] != "ok")

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
    ])

    import_result = make_import_smoke(a10q)

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

    final_counts = {
        "safe_quarantine_candidate_count": a10o.get("a10f_safe_quarantine_candidate_count"),
        "referenced_keep_count": a10o.get("referenced_keep_count"),
        "historical_placeholder_keep_count": a10o.get("historical_placeholder_keep_count"),
        "compat_required_count": a10o.get("compat_required_count"),
        "compat_apply_candidate_count": a10p.get("apply_candidate_count"),
        "compat_keep_allowlist_count": a10p.get("keep_allowlist_count"),
        "compat_applied_count": a10q.get("applied_count"),
        "compat_failed_count": a10q.get("failed_count"),
        "unclassified_count": a10o.get("unclassified_count"),
        "non_placeholder_low_risk_count": a10o.get("non_placeholder_low_risk_count"),
    }

    ok = (
        a10n.get("ok") is True
        and a10o.get("ok") is True
        and a10p.get("ok") is True
        and a10q.get("ok") is True
        and final_counts["safe_quarantine_candidate_count"] == 0
        and final_counts["referenced_keep_count"] == 45
        and final_counts["historical_placeholder_keep_count"] == 7
        and final_counts["compat_required_count"] == 7
        and final_counts["compat_apply_candidate_count"] == 3
        and final_counts["compat_keep_allowlist_count"] == 4
        and final_counts["compat_applied_count"] == 3
        and final_counts["compat_failed_count"] == 0
        and final_counts["unclassified_count"] == 0
        and final_counts["non_placeholder_low_risk_count"] == 0
        and wrapper_not_ok_count == 0
        and compile_result["returncode"] == 0
        and import_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10R_FINAL_TECH_DEBT_EVIDENCE",
        "ok": ok,
        "decision": "A10R_FINAL_TECH_DEBT_EVIDENCE_GREEN" if ok else "A10R_FINAL_TECH_DEBT_EVIDENCE_NOT_GREEN",
        "source_reports": {
            "a10n": str(A10N_JSON),
            "a10o": str(A10O_JSON),
            "a10p": str(A10P_JSON),
            "a10q": str(A10Q_JSON),
        },
        "final_counts": final_counts,
        "wrapper_check_count": len(wrapper_checks),
        "wrapper_not_ok_count": wrapper_not_ok_count,
        "wrapper_checks": wrapper_checks,
        "compileall_returncode": compile_result["returncode"],
        "import_smoke_returncode": import_result["returncode"],
        "import_smoke_tail": import_result["combined"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "pytest_tail": pytest_result["combined"],
        "remaining_quality_work": {
            "warnings": pytest_summary.get("warnings", 0),
            "next_phase": "A11_WARNING_ZERO",
            "note": "A10 teknik borç temizliği kapandı; kalan 32 warning A11 Warning Zero fazının konusudur.",
        },
        "live_note": "Bu A10 kapanışı local/repo kalite kanıtıdır. Canlı ortam için ayrıca gerçek .env, Sentry DSN, DB SSL/TLS, canlı backup ve URL smoke gate yapılmalıdır.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10R Final Teknik Borç Evidence",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Import smoke returncode: {result['import_smoke_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## Final Sayımlar",
        "",
        "```json",
        json.dumps(result["final_counts"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Wrapper Kontrolü",
        "",
        f"- Wrapper check count: {result['wrapper_check_count']}",
        f"- Wrapper not OK count: {result['wrapper_not_ok_count']}",
        "",
        "```json",
        json.dumps(result["wrapper_checks"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Import Smoke",
        "",
        "```text",
        result["import_smoke_tail"],
        "```",
        "",
        "## Pytest Özeti",
        "",
        "```json",
        json.dumps(result["pytest_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Kalan Kalite İşi",
        "",
        "```json",
        json.dumps(result["remaining_quality_work"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Canlı Notu",
        "",
        result["live_note"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    evidence_files = collect_evidence_files()

    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in evidence_files:
            zf.write(file, rel(file))

    sha = sha256_file(OUT_ZIP)

    # ZIP bilgilerini JSON/MD rapora sonradan işle
    result["evidence_zip"] = str(OUT_ZIP)
    result["evidence_zip_sha256"] = sha
    result["evidence_file_count"] = len(evidence_files)

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines.extend([
        "",
        "## Evidence ZIP",
        "",
        f"- ZIP: `{OUT_ZIP}`",
        f"- SHA256: `{sha}`",
        f"- Evidence file count: {len(evidence_files)}",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    # Son JSON/MD halini ZIP içine güncelle
    with zipfile.ZipFile(OUT_ZIP, "a", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(OUT_JSON, rel(OUT_JSON))
        zf.write(OUT_MD, rel(OUT_MD))

    print("A10R_REPORT_JSON:", OUT_JSON)
    print("A10R_REPORT_MD:", OUT_MD)
    print("A10R_EVIDENCE_ZIP:", OUT_ZIP)
    print("A10R_EVIDENCE_ZIP_SHA256:", sha)
    print("A10R_EVIDENCE_FILE_COUNT:", len(evidence_files))
    print("A10R_FINAL_COUNTS:", json.dumps(final_counts, ensure_ascii=False))
    print("A10R_WRAPPER_CHECK_COUNT:", result["wrapper_check_count"])
    print("A10R_WRAPPER_NOT_OK_COUNT:", result["wrapper_not_ok_count"])
    print("A10R_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A10R_IMPORT_SMOKE_RETURN_CODE:", result["import_smoke_returncode"])
    print("A10R_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A10R_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A10R_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
