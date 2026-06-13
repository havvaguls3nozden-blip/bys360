from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import hashlib
import json
import os
import re
import subprocess
import zipfile

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

OUT_JSON = QUALITY / "BYS360_S0Z_SECURITY_TEST_HYGIENE_FINAL_CLOSURE.json"
OUT_MD = QUALITY / "BYS360_S0Z_SECURITY_TEST_HYGIENE_FINAL_CLOSURE.md"
ZIP_PATH = RELEASES / f"BYS360_S0Z_SECURITY_TEST_HYGIENE_FINAL_CLOSURE_{STAMP}.zip"

S0A_SCRIPT = ROOT / "scripts" / "quality" / "bys360_s0a_claude_findings_verification_audit.py"
S0A_JSON = QUALITY / "BYS360_S0A_CLAUDE_FINDINGS_VERIFICATION_AUDIT.json"

PHASE_REPORTS = {
    "S0C3": QUALITY / "BYS360_S0C3_REMAINING_SECRETKEY_BLOCK_HOTFIX.json",
    "S0D": QUALITY / "BYS360_S0D_PYTEST_CONFIG_BACKUP_COLLECTION_HOTFIX.json",
    "S0E": QUALITY / "BYS360_S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_CLEANUP.json",
    "S0F3": QUALITY / "BYS360_S0F3_PYTEST_ISOLATED_UPDATE_VERIFY.json",
    "S0G": QUALITY / "BYS360_S0G_OLD_VENV_ARCHIVE_CLEANUP.json",
}

PHASE_MARKDOWN = [
    QUALITY / "BYS360_S0C3_REMAINING_SECRETKEY_BLOCK_HOTFIX.md",
    QUALITY / "BYS360_S0D_PYTEST_CONFIG_BACKUP_COLLECTION_HOTFIX.md",
    QUALITY / "BYS360_S0E_REPORTS_QUALITY_BACKUP_ARCHIVE_CLEANUP.md",
    QUALITY / "BYS360_S0F3_PYTEST_ISOLATED_UPDATE_VERIFY.md",
    QUALITY / "BYS360_S0G_OLD_VENV_ARCHIVE_CLEANUP.md",
]


def run_cmd(cmd, timeout=1800):
    try:
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
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-30000:],
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="ignore")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="ignore")
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 124,
            "stdout": stdout,
            "stderr": stderr,
            "combined_tail": (stdout + "\n" + stderr + "\nTIMEOUT")[-30000:],
        }


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"_missing": True, "path": str(path)}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc), "path": str(path)}


def parse_pytest_summary(text: str) -> dict:
    summary = {}
    pattern = r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warning|warnings)\b"

    for num, key in re.findall(pattern, text or "", flags=re.IGNORECASE):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)

    for key in ["failed", "passed", "errors", "skipped", "deselected", "warnings"]:
        summary.setdefault(key, 0)

    return summary


def parse_audit_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
    return {}


def run_pip_audit(py: Path) -> dict:
    attempts = [
        [str(py), "-m", "pip_audit", "-f", "json"],
        [str(ROOT / ".venv" / "Scripts" / "pip-audit.exe"), "-f", "json"],
        ["pip-audit", "-f", "json"],
    ]

    tried = []

    for cmd in attempts:
        result = run_cmd(cmd, timeout=1800)
        tried.append({
            "cmd": result["cmd"],
            "returncode": result["returncode"],
            "tail": result["combined_tail"][-2000:],
        })

        data = parse_audit_json(result["stdout"] or result["combined_tail"])
        if data:
            findings = []
            for dep in data.get("dependencies") or []:
                name = str(dep.get("name") or "").lower()
                version = str(dep.get("version") or "")
                for vuln in dep.get("vulns") or []:
                    findings.append({
                        "package": name,
                        "installed_version": version,
                        "vulnerability_id": vuln.get("id"),
                        "aliases": vuln.get("aliases") or [],
                    })

            return {
                "available": True,
                "command": result["cmd"],
                "returncode": result["returncode"],
                "vulnerability_count": len(findings),
                "by_package": dict(Counter(item["package"] for item in findings)),
                "findings": findings,
                "attempts": tried,
            }

    return {
        "available": False,
        "command": None,
        "returncode": 127,
        "vulnerability_count": None,
        "by_package": {},
        "findings": [],
        "attempts": tried,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_if_exists(zf: zipfile.ZipFile, path: Path, arcname: str | None = None):
    if path.exists() and path.is_file():
        zf.write(path, arcname or path.relative_to(ROOT).as_posix())


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    s0a_proc = {"returncode": None}
    if S0A_SCRIPT.exists():
        s0a_proc = run_cmd([str(py), str(S0A_SCRIPT)], timeout=1200)

    s0a = read_json(S0A_JSON)

    phase_status = {}
    for name, path in PHASE_REPORTS.items():
        data = read_json(path)
        phase_status[name] = {
            "path": str(path),
            "exists": path.exists(),
            "ok": data.get("ok"),
            "decision": data.get("decision"),
            "generated_at": data.get("generated_at"),
        }

    compile_result = run_cmd([
        str(py),
        "-m",
        "compileall",
        "-q",
        "config.py",
        "app",
        "scripts",
        "migrations",
    ])

    collect_result = run_cmd([
        str(py),
        "-m",
        "pytest",
        "--collect-only",
        "-q",
    ], timeout=900)

    quality_smoke = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests/quality",
        "-m",
        "ci_safe",
        "-q",
        "-ra",
    ], timeout=900)

    full_pytest = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ], timeout=1800)

    default_pytest = run_cmd([
        str(py),
        "-m",
        "pytest",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ], timeout=1800)

    quality_summary = parse_pytest_summary(quality_smoke["combined_tail"])
    full_summary = parse_pytest_summary(full_pytest["combined_tail"])
    default_summary = parse_pytest_summary(default_pytest["combined_tail"])

    pip_audit = run_pip_audit(py)

    red_flag_count = s0a.get("red_flag_count")
    pip_audit_count_s0a = (
        s0a.get("checks", {})
        .get("pip_audit", {})
        .get("vulnerability_count")
    )
    old_venv_total_mb_s0a = (
        s0a.get("checks", {})
        .get("old_venvs", {})
        .get("old_venv_total_mb")
    )

    all_phase_reports_green = all(item["ok"] is True for item in phase_status.values())

    tests_green = (
        compile_result["returncode"] == 0
        and collect_result["returncode"] == 0
        and quality_smoke["returncode"] == 0
        and full_pytest["returncode"] == 0
        and default_pytest["returncode"] == 0
        and full_summary.get("failed", 0) == 0
        and full_summary.get("errors", 0) == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and full_summary.get("passed", 0) >= 700
        and default_summary.get("passed", 0) >= 700
    )

    security_green = (
        s0a_proc.get("returncode") in {0, None}
        and s0a.get("ok") is True
        and red_flag_count == 0
        and pip_audit["available"] is True
        and pip_audit["vulnerability_count"] == 0
        and pip_audit_count_s0a in {0, None}
        and old_venv_total_mb_s0a in {0, 0.0, None}
    )

    ok = all_phase_reports_green and tests_green and security_green

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0Z_SECURITY_TEST_HYGIENE_FINAL_CLOSURE",
        "mode": "final_evidence_report_no_code_change",
        "ok": ok,
        "decision": "S0Z_GREEN_READY_FOR_PHASE2_ARCHITECTURE" if ok else "S0Z_REVIEW_REQUIRED",
        "phase_status": phase_status,
        "s0a_rerun": {
            "returncode": s0a_proc.get("returncode"),
            "ok": s0a.get("ok"),
            "red_flag_count": red_flag_count,
            "pip_audit_vulnerability_count": pip_audit_count_s0a,
            "old_venv_total_mb": old_venv_total_mb_s0a,
        },
        "pip_audit": pip_audit,
        "compileall_returncode": compile_result["returncode"],
        "collect_only_returncode": collect_result["returncode"],
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": quality_summary,
        "pytest_full_returncode": full_pytest["returncode"],
        "pytest_full_summary": full_summary,
        "pytest_default_returncode": default_pytest["returncode"],
        "pytest_default_summary": default_summary,
        "all_phase_reports_green": all_phase_reports_green,
        "tests_green": tests_green,
        "security_green": security_green,
        "next_action": "Faz 2A mimari borç haritasına geçilebilir." if ok else "S0Z raporu incelenmeli; kırmızı kalan başlık kapatılmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 S0Z Güvenlik ve Test Hijyeni Final Kapanış Raporu",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- All phase reports green: {all_phase_reports_green}",
        f"- Tests green: {tests_green}",
        f"- Security green: {security_green}",
        f"- S0A red flag count: {red_flag_count}",
        f"- Pip-audit vulnerability count: {pip_audit['vulnerability_count']}",
        f"- S0A old venv total MB: {old_venv_total_mb_s0a}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Collect-only returncode: {result['collect_only_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        f"- Pytest full returncode: {result['pytest_full_returncode']}",
        f"- Pytest default returncode: {result['pytest_default_returncode']}",
        "",
        "## Faz Durumları",
        "",
        "```json",
        json.dumps(phase_status, ensure_ascii=False, indent=2),
        "```",
        "",
        "## S0A Rerun",
        "",
        "```json",
        json.dumps(result["s0a_rerun"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pip-Audit",
        "",
        "```json",
        json.dumps({
            "available": pip_audit["available"],
            "returncode": pip_audit["returncode"],
            "vulnerability_count": pip_audit["vulnerability_count"],
            "by_package": pip_audit["by_package"],
        }, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Full Summary",
        "",
        "```json",
        json.dumps(full_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Default Summary",
        "",
        "```json",
        json.dumps(default_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        add_if_exists(zf, OUT_JSON)
        add_if_exists(zf, OUT_MD)

        for path in PHASE_REPORTS.values():
            add_if_exists(zf, path)

        for path in PHASE_MARKDOWN:
            add_if_exists(zf, path)

        add_if_exists(zf, S0A_JSON)
        add_if_exists(zf, QUALITY / "BYS360_S0F3_PRE_UPDATE_PIP_FREEZE.txt")
        add_if_exists(zf, QUALITY / "BYS360_S0F3_POST_UPDATE_PIP_FREEZE.txt")
        add_if_exists(zf, QUALITY / "BYS360_S0F2_VERIFY_PIP_FREEZE.txt")

    zip_sha256 = sha256_file(ZIP_PATH)

    result["release_zip"] = str(ZIP_PATH)
    result["release_zip_sha256"] = zip_sha256
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("S0Z_REPORT_JSON:", OUT_JSON)
    print("S0Z_REPORT_MD:", OUT_MD)
    print("S0Z_RELEASE_ZIP:", ZIP_PATH)
    print("S0Z_RELEASE_ZIP_SHA256:", zip_sha256)
    print("S0Z_ALL_PHASE_REPORTS_GREEN:", all_phase_reports_green)
    print("S0Z_TESTS_GREEN:", tests_green)
    print("S0Z_SECURITY_GREEN:", security_green)
    print("S0Z_S0A_RED_FLAG_COUNT:", red_flag_count)
    print("S0Z_PIP_AUDIT_VULNERABILITY_COUNT:", pip_audit["vulnerability_count"])
    print("S0Z_OLD_VENV_TOTAL_MB:", old_venv_total_mb_s0a)
    print("S0Z_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0Z_COLLECT_ONLY_RETURN_CODE:", result["collect_only_returncode"])
    print("S0Z_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0Z_PYTEST_FULL_RETURN_CODE:", result["pytest_full_returncode"])
    print("S0Z_PYTEST_FULL_SUMMARY:", json.dumps(full_summary, ensure_ascii=False))
    print("S0Z_PYTEST_DEFAULT_RETURN_CODE:", result["pytest_default_returncode"])
    print("S0Z_PYTEST_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("S0Z_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
