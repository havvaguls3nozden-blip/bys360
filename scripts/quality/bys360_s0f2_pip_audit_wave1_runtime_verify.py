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

OUT_JSON = QUALITY / "BYS360_S0F2_PIP_AUDIT_WAVE1_RUNTIME_VERIFY.json"
OUT_MD = QUALITY / "BYS360_S0F2_PIP_AUDIT_WAVE1_RUNTIME_VERIFY.md"

S0A_SCRIPT = ROOT / "scripts" / "quality" / "bys360_s0a_claude_findings_verification_audit.py"
S0A_JSON = QUALITY / "BYS360_S0A_CLAUDE_FINDINGS_VERIFICATION_AUDIT.json"

WAVE1_PACKAGES = {
    "cryptography",
    "flask",
    "pillow",
    "python-dotenv",
    "waitress",
}

DEFERRED_PACKAGES = {
    "pytest",
}


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
            "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-24000:],
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
            "combined_tail": (stdout + "\n" + stderr + "\nTIMEOUT")[-24000:],
        }


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


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc)}


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


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    pip_list = run_cmd([str(py), "-m", "pip", "list", "--format=json"], timeout=600)
    package_versions = parse_pip_list(pip_list["stdout"])

    freeze = run_cmd([str(py), "-m", "pip", "freeze"], timeout=600)
    (QUALITY / "BYS360_S0F2_VERIFY_PIP_FREEZE.txt").write_text(
        freeze["stdout"],
        encoding="utf-8",
    )

    audit = run_pip_audit(py)
    findings = normalize_audit_findings(audit["data"])

    by_package = Counter(item["package"] for item in findings)
    wave1_findings = [item for item in findings if item["package"] in WAVE1_PACKAGES]
    deferred_findings = [item for item in findings if item["package"] in DEFERRED_PACKAGES]
    other_findings = [
        item for item in findings
        if item["package"] not in WAVE1_PACKAGES
        and item["package"] not in DEFERRED_PACKAGES
    ]

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

    quality_summary = parse_pytest_summary(quality_smoke["combined_tail"])
    full_summary = parse_pytest_summary(full_pytest["combined_tail"])
    default_summary = parse_pytest_summary(default_pytest["combined_tail"])

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
        audit["available"] is True
        and len(wave1_findings) == 0
        and len(other_findings) == 0
        and compile_result["returncode"] == 0
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

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0F2_PIP_AUDIT_WAVE1_RUNTIME_VERIFY",
        "mode": "verify_after_runtime_dependency_update",
        "ok": ok,
        "decision": "S0F2_GREEN_RUNTIME_FIXED" if ok else "S0F2_REVIEW_REQUIRED",
        "package_versions": {
            name: package_versions.get(name)
            for name in sorted(WAVE1_PACKAGES | DEFERRED_PACKAGES)
        },
        "pip_audit_available": audit["available"],
        "pip_audit_command": audit["command"],
        "pip_audit_returncode": audit["returncode"],
        "vulnerability_count_after": len(findings),
        "by_package_after": dict(by_package),
        "wave1_vulnerability_count_after": len(wave1_findings),
        "deferred_vulnerability_count_after": len(deferred_findings),
        "other_vulnerability_count_after": len(other_findings),
        "remaining_findings": findings,
        "deferred_findings": deferred_findings,
        "other_findings": other_findings,
        "compileall_returncode": compile_result["returncode"],
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": quality_summary,
        "pytest_full_returncode": full_pytest["returncode"],
        "pytest_full_summary": full_summary,
        "pytest_default_returncode": default_pytest["returncode"],
        "pytest_default_summary": default_summary,
        "s0a_rerun": s0a_rerun,
        "next_action": (
            "S0F3 pytest zafiyeti için ayrı test-altyapısı dalgası değerlendirilebilir; riskli bulunursa S0G eski venv temizliğine geçilebilir."
            if ok else
            "S0F2 raporu incelenmeli; wave1 paketlerden biri hâlâ zafiyetli veya test kırılmış olabilir."
        ),
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 S0F2 Pip-Audit Wave1 Runtime Verify",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Vulnerability count after: {result['vulnerability_count_after']}",
        f"- Wave1 vulnerability count after: {result['wave1_vulnerability_count_after']}",
        f"- Deferred vulnerability count after: {result['deferred_vulnerability_count_after']}",
        f"- Other vulnerability count after: {result['other_vulnerability_count_after']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        f"- Pytest full returncode: {result['pytest_full_returncode']}",
        f"- Pytest default returncode: {result['pytest_default_returncode']}",
        "",
        "## Package Versions",
        "",
        "```json",
        json.dumps(result["package_versions"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## By Package After",
        "",
        "```json",
        json.dumps(result["by_package_after"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Remaining Findings",
        "",
        "```json",
        json.dumps(result["remaining_findings"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## S0A Rerun",
        "",
        "```json",
        json.dumps(s0a_rerun, ensure_ascii=False, indent=2),
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

    print("S0F2_REPORT_JSON:", OUT_JSON)
    print("S0F2_REPORT_MD:", OUT_MD)
    print("S0F2_PIP_AUDIT_AVAILABLE:", result["pip_audit_available"])
    print("S0F2_PIP_AUDIT_RETURN_CODE:", result["pip_audit_returncode"])
    print("S0F2_VULNERABILITY_COUNT_AFTER:", result["vulnerability_count_after"])
    print("S0F2_BY_PACKAGE_AFTER:", json.dumps(dict(by_package), ensure_ascii=False))
    print("S0F2_WAVE1_VULNERABILITY_COUNT_AFTER:", result["wave1_vulnerability_count_after"])
    print("S0F2_DEFERRED_VULNERABILITY_COUNT_AFTER:", result["deferred_vulnerability_count_after"])
    print("S0F2_OTHER_VULNERABILITY_COUNT_AFTER:", result["other_vulnerability_count_after"])
    print("S0F2_PACKAGE_VERSIONS:", json.dumps(result["package_versions"], ensure_ascii=False))
    print("S0F2_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0F2_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0F2_PYTEST_FULL_RETURN_CODE:", result["pytest_full_returncode"])
    print("S0F2_PYTEST_FULL_SUMMARY:", json.dumps(full_summary, ensure_ascii=False))
    print("S0F2_PYTEST_DEFAULT_RETURN_CODE:", result["pytest_default_returncode"])
    print("S0F2_PYTEST_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("S0F2_S0A_PIP_AUDIT_VULNERABILITY_COUNT:", s0a_rerun.get("pip_audit_vulnerability_count"))
    print("S0F2_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
