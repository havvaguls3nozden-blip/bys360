from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

OUT_JSON = QUALITY / "BYS360_S0F3_PYTEST_ISOLATED_UPDATE_VERIFY.json"
OUT_MD = QUALITY / "BYS360_S0F3_PYTEST_ISOLATED_UPDATE_VERIFY.md"
ROLLBACK_PS1 = QUALITY / "BYS360_S0F3_ROLLBACK_PYTEST.ps1"

S0A_SCRIPT = ROOT / "scripts" / "quality" / "bys360_s0a_claude_findings_verification_audit.py"
S0A_JSON = QUALITY / "BYS360_S0A_MAINTENANCE_FINDINGS_VERIFICATION_AUDIT.json"

TARGET_SPEC = "pytest>=9.0.3"


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
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc)}


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


def parse_version_key(value: str):
    parts = re.findall(r"\d+|[a-zA-Z]+", value or "")
    key = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part.lower()))
    return key


def version_gte(current: str | None, target: str) -> bool:
    if not current:
        return False
    return parse_version_key(current) >= parse_version_key(target)


def parse_pip_list(text: str) -> dict:
    try:
        rows = json.loads(text)
    except Exception:
        return {}

    result = {}
    for row in rows:
        name = str(row.get("name") or "").lower()
        version = str(row.get("version") or "")
        if name:
            result[name] = version

    return result


def pip_list(py: Path) -> dict:
    result = run_cmd([str(py), "-m", "pip", "list", "--format=json"], timeout=600)
    return parse_pip_list(result["stdout"])


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
            return {
                "available": True,
                "command": result["cmd"],
                "returncode": result["returncode"],
                "data": data,
                "attempts": tried,
            }

    return {
        "available": False,
        "command": None,
        "returncode": 127,
        "data": {},
        "attempts": tried,
    }


def normalize_audit_findings(audit_data: dict) -> list[dict]:
    findings = []

    deps = audit_data.get("dependencies") or []
    for dep in deps:
        name = str(dep.get("name") or "").lower()
        version = str(dep.get("version") or "")
        vulns = dep.get("vulns") or []

        for vuln in vulns:
            findings.append({
                "package": name,
                "installed_version": version,
                "vulnerability_id": vuln.get("id"),
                "aliases": vuln.get("aliases") or [],
                "fix_versions": vuln.get("fix_versions") or [],
                "description_present": bool(vuln.get("description")),
            })

    return findings


def write_rollback_script(old_pytest_version: str | None) -> None:
    lines = [
        '$ErrorActionPreference = "Stop"',
        'cd C:\\bys360\\project',
        '',
    ]

    if old_pytest_version:
        lines.extend([
            f'.\\.venv\\Scripts\\python.exe -m pip install --force-reinstall "pytest=={old_pytest_version}"',
            '.\\.venv\\Scripts\\python.exe -m pytest -m "not live and not realdb and not slow" -q -ra',
        ])
    else:
        lines.append('Write-Host "Eski pytest sürümü bulunamadı; manuel kontrol gerekli."')

    ROLLBACK_PS1.write_text("\n".join(lines), encoding="utf-8")


def run_validation(py: Path) -> dict:
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

    return {
        "compileall_returncode": compile_result["returncode"],
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": parse_pytest_summary(quality_smoke["combined_tail"]),
        "pytest_full_returncode": full_pytest["returncode"],
        "pytest_full_summary": parse_pytest_summary(full_pytest["combined_tail"]),
        "pytest_default_returncode": default_pytest["returncode"],
        "pytest_default_summary": parse_pytest_summary(default_pytest["combined_tail"]),
    }


def validation_green(validation: dict) -> bool:
    full_summary = validation["pytest_full_summary"]
    default_summary = validation["pytest_default_summary"]

    return (
        validation["compileall_returncode"] == 0
        and validation["pytest_quality_smoke_returncode"] == 0
        and validation["pytest_full_returncode"] == 0
        and validation["pytest_default_returncode"] == 0
        and full_summary.get("failed", 0) == 0
        and full_summary.get("errors", 0) == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and full_summary.get("passed", 0) >= 700
        and default_summary.get("passed", 0) >= 700
    )


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    pre_versions = pip_list(py)
    pre_pytest_version = pre_versions.get("pytest")

    write_rollback_script(pre_pytest_version)

    pre_freeze = run_cmd([str(py), "-m", "pip", "freeze"], timeout=600)
    (QUALITY / "BYS360_S0F3_PRE_UPDATE_PIP_FREEZE.txt").write_text(
        pre_freeze["stdout"],
        encoding="utf-8",
    )

    install_result = run_cmd([
        str(py),
        "-m",
        "pip",
        "install",
        "--upgrade",
        TARGET_SPEC,
    ], timeout=1800)

    post_versions = pip_list(py)
    post_pytest_version = post_versions.get("pytest")

    validation = run_validation(py)

    rollback_performed = False
    rollback_result = None
    rollback_validation = None

    if install_result["returncode"] != 0 or not validation_green(validation):
        rollback_performed = True
        if pre_pytest_version:
            rollback_result = run_cmd([
                str(py),
                "-m",
                "pip",
                "install",
                "--force-reinstall",
                f"pytest=={pre_pytest_version}",
            ], timeout=1800)
            rollback_validation = run_validation(py)

    final_versions = pip_list(py)

    post_freeze = run_cmd([str(py), "-m", "pip", "freeze"], timeout=600)
    (QUALITY / "BYS360_S0F3_POST_UPDATE_PIP_FREEZE.txt").write_text(
        post_freeze["stdout"],
        encoding="utf-8",
    )

    audit = run_pip_audit(py)
    findings = normalize_audit_findings(audit["data"])
    by_package = Counter(item["package"] for item in findings)

    s0a_rerun = {"returncode": None}
    if S0A_SCRIPT.exists():
        s0a_proc = run_cmd([str(py), str(S0A_SCRIPT)], timeout=1200)
        s0a_json = read_json(S0A_JSON)
        s0a_rerun = {
            "returncode": s0a_proc["returncode"],
            "ok": s0a_json.get("ok"),
            "red_flag_count": s0a_json.get("red_flag_count"),
            "pip_audit_available": (
                s0a_json.get("checks", {})
                .get("pip_audit", {})
                .get("available")
            ),
            "pip_audit_vulnerability_count": (
                s0a_json.get("checks", {})
                .get("pip_audit", {})
                .get("vulnerability_count")
            ),
            "old_venv_total_mb": (
                s0a_json.get("checks", {})
                .get("old_venvs", {})
                .get("old_venv_total_mb")
            ),
        }

    ok = (
        rollback_performed is False
        and install_result["returncode"] == 0
        and version_gte(final_versions.get("pytest"), "9.0.3")
        and validation_green(validation)
        and audit["available"] is True
        and len(findings) == 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0F3_PYTEST_ISOLATED_UPDATE_VERIFY",
        "mode": "isolated_test_tool_update_with_auto_rollback_on_test_failure",
        "ok": ok,
        "decision": "S0F3_GREEN_ALL_PIP_AUDIT_FIXED" if ok else "S0F3_REVIEW_OR_ROLLBACK_PERFORMED",
        "target_spec": TARGET_SPEC,
        "rollback_script": str(ROLLBACK_PS1),
        "pre_pytest_version": pre_pytest_version,
        "post_pytest_version": post_pytest_version,
        "final_pytest_version": final_versions.get("pytest"),
        "install_returncode": install_result["returncode"],
        "rollback_performed": rollback_performed,
        "rollback_returncode": rollback_result["returncode"] if rollback_result else None,
        "validation_after_update": validation,
        "rollback_validation": rollback_validation,
        "pip_audit_available": audit["available"],
        "pip_audit_returncode": audit["returncode"],
        "pip_audit_vulnerability_count_after": len(findings),
        "pip_audit_by_package_after": dict(by_package),
        "remaining_findings": findings,
        "s0a_rerun": s0a_rerun,
        "next_action": "S0G eski .venv_old_* temizliğine geçilebilir." if ok else "S0F3 raporu incelenmeli; rollback yapılmışsa test zemini eski pytest ile korunmuştur.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 S0F3 Pytest Isolated Update Verify",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Target spec: `{result['target_spec']}`",
        f"- Rollback script: `{result['rollback_script']}`",
        f"- Pre pytest version: {result['pre_pytest_version']}",
        f"- Post pytest version: {result['post_pytest_version']}",
        f"- Final pytest version: {result['final_pytest_version']}",
        f"- Install returncode: {result['install_returncode']}",
        f"- Rollback performed: {result['rollback_performed']}",
        f"- Pip-audit vulnerability count after: {result['pip_audit_vulnerability_count_after']}",
        "",
        "## Validation After Update",
        "",
        "```json",
        json.dumps(validation, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pip-Audit By Package After",
        "",
        "```json",
        json.dumps(dict(by_package), ensure_ascii=False, indent=2),
        "```",
        "",
        "## Remaining Findings",
        "",
        "```json",
        json.dumps(findings, ensure_ascii=False, indent=2),
        "```",
        "",
        "## S0A Rerun",
        "",
        "```json",
        json.dumps(s0a_rerun, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("S0F3_REPORT_JSON:", OUT_JSON)
    print("S0F3_REPORT_MD:", OUT_MD)
    print("S0F3_ROLLBACK_PS1:", ROLLBACK_PS1)
    print("S0F3_PRE_PYTEST_VERSION:", pre_pytest_version)
    print("S0F3_POST_PYTEST_VERSION:", post_pytest_version)
    print("S0F3_FINAL_PYTEST_VERSION:", final_versions.get("pytest"))
    print("S0F3_INSTALL_RETURN_CODE:", install_result["returncode"])
    print("S0F3_ROLLBACK_PERFORMED:", rollback_performed)
    print("S0F3_COMPILEALL_RETURN_CODE:", validation["compileall_returncode"])
    print("S0F3_PYTEST_QUALITY_SMOKE_RETURN_CODE:", validation["pytest_quality_smoke_returncode"])
    print("S0F3_PYTEST_FULL_RETURN_CODE:", validation["pytest_full_returncode"])
    print("S0F3_PYTEST_FULL_SUMMARY:", json.dumps(validation["pytest_full_summary"], ensure_ascii=False))
    print("S0F3_PYTEST_DEFAULT_RETURN_CODE:", validation["pytest_default_returncode"])
    print("S0F3_PYTEST_DEFAULT_SUMMARY:", json.dumps(validation["pytest_default_summary"], ensure_ascii=False))
    print("S0F3_PIP_AUDIT_VULNERABILITY_COUNT_AFTER:", len(findings))
    print("S0F3_PIP_AUDIT_BY_PACKAGE_AFTER:", json.dumps(dict(by_package), ensure_ascii=False))
    print("S0F3_S0A_RED_FLAG_COUNT:", s0a_rerun.get("red_flag_count"))
    print("S0F3_S0A_PIP_AUDIT_VULNERABILITY_COUNT:", s0a_rerun.get("pip_audit_vulnerability_count"))
    print("S0F3_S0A_OLD_VENV_TOTAL_MB:", s0a_rerun.get("old_venv_total_mb"))
    print("S0F3_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
