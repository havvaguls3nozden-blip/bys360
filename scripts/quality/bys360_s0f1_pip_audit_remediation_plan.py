from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

OUT_JSON = QUALITY / "BYS360_S0F1_PIP_AUDIT_REMEDIATION_PLAN.json"
OUT_MD = QUALITY / "BYS360_S0F1_PIP_AUDIT_REMEDIATION_PLAN.md"
APPLY_PS1 = QUALITY / "BYS360_S0F2_APPLY_PIP_AUDIT_WAVE1_RUNTIME.ps1"

S0A_SCRIPT = ROOT / "scripts" / "quality" / "bys360_s0a_claude_findings_verification_audit.py"
S0A_JSON = QUALITY / "BYS360_S0A_MAINTENANCE_FINDINGS_VERIFICATION_AUDIT.json"

RUNTIME_PRIORITY = {
    "flask",
    "waitress",
    "pillow",
    "cryptography",
    "python-dotenv",
    "werkzeug",
    "jinja2",
    "itsdangerous",
    "click",
    "requests",
    "urllib3",
    "sqlalchemy",
    "alembic",
    "psycopg2",
    "psycopg2-binary",
}

LOWER_RUNTIME_PRIORITY = {
    "setuptools",
    "pip",
    "wheel",
    "certifi",
    "idna",
    "charset-normalizer",
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


def choose_fix_version(fix_versions: list[str]) -> str | None:
    clean = [x for x in fix_versions if isinstance(x, str) and x.strip()]
    if not clean:
        return None
    return sorted(clean, key=parse_version_key)[0]


def find_requirement_files() -> list[str]:
    names = []
    for pattern in ["requirements*.txt", "constraints*.txt"]:
        for path in ROOT.rglob(pattern):
            rel = path.relative_to(ROOT).as_posix()
            if any(part in rel.lower().split("/") for part in [".venv", "venv", "node_modules", "reports", "releases"]):
                continue
            names.append(rel)
    return sorted(set(names))


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
            fix_versions = vuln.get("fix_versions") or []
            fix_version = choose_fix_version(fix_versions)

            findings.append({
                "package": name,
                "installed_version": version,
                "vulnerability_id": vuln.get("id"),
                "aliases": vuln.get("aliases") or [],
                "description_present": bool(vuln.get("description")),
                "fix_versions": fix_versions,
                "chosen_fix_version": fix_version,
                "has_fix": bool(fix_version),
            })

    return findings


def classify_package(package: str) -> str:
    p = package.lower()

    if p in RUNTIME_PRIORITY:
        return "wave1_runtime_priority"

    if p in LOWER_RUNTIME_PRIORITY:
        return "wave2_runtime_support"

    return "wave3_manual_or_transitive_review"


def build_upgrade_groups(findings: list[dict]) -> dict:
    package_to_fix = {}

    for item in findings:
        package = item["package"]
        fix = item["chosen_fix_version"]

        if not fix:
            continue

        old = package_to_fix.get(package)
        if old is None or parse_version_key(fix) > parse_version_key(old):
            package_to_fix[package] = fix

    groups = defaultdict(list)

    for package, fix in sorted(package_to_fix.items()):
        wave = classify_package(package)
        groups[wave].append({
            "package": package,
            "target_min_version": fix,
            "pip_spec": f"{package}>={fix}",
        })

    return dict(groups)


def write_apply_script(groups: dict) -> None:
    wave1 = groups.get("wave1_runtime_priority", [])

    lines = [
        '$ErrorActionPreference = "Stop"',
        'cd C:\\bys360\\project',
        '',
        'Write-Host "S0F2 Wave1 runtime dependency update başlıyor..."',
        'Write-Host "Önce mevcut paket listesi yedekleniyor..."',
        '.\\.venv\\Scripts\\python.exe -m pip freeze | Set-Content -Path ".\\reports\\quality\\BYS360_S0F2_PRE_UPDATE_PIP_FREEZE.txt" -Encoding UTF8',
        '',
    ]

    if wave1:
        specs = " ".join([f'"{item["pip_spec"]}"' for item in wave1])
        lines.extend([
            'Write-Host "Wave1 runtime paketleri güncelleniyor..."',
            f'.\\.venv\\Scripts\\python.exe -m pip install --upgrade {specs}',
            '',
        ])
    else:
        lines.extend([
            'Write-Host "Wave1 runtime priority paketi bulunmadı; güncelleme yapılmayacak."',
            '',
        ])

    lines.extend([
        'Write-Host "Kurulum sonrası freeze alınıyor..."',
        '.\\.venv\\Scripts\\python.exe -m pip freeze | Set-Content -Path ".\\reports\\quality\\BYS360_S0F2_POST_UPDATE_PIP_FREEZE.txt" -Encoding UTF8',
        '',
        'Write-Host "S0F2 sonrası compile/test/audit kanıtı için bir sonraki doğrulama scripti çalıştırılmalı."',
    ])

    APPLY_PS1.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    freeze_result = run_cmd([str(py), "-m", "pip", "freeze"], timeout=600)
    pip_list_result = run_cmd([str(py), "-m", "pip", "list", "--format=json"], timeout=600)
    audit = run_pip_audit(py)
    findings = normalize_audit_findings(audit["data"])

    by_package = Counter(item["package"] for item in findings)
    by_has_fix = Counter("has_fix" if item["has_fix"] else "no_fix" for item in findings)

    groups = build_upgrade_groups(findings)
    write_apply_script(groups)

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
    default_summary = parse_pytest_summary(default_pytest["combined_tail"])

    requirement_files = find_requirement_files()

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

    vuln_count = len(findings)
    packages_with_vulns = sorted(by_package.keys())
    no_fix_count = by_has_fix.get("no_fix", 0)

    ok = (
        audit["available"] is True
        and compile_result["returncode"] == 0
        and quality_smoke["returncode"] == 0
        and default_pytest["returncode"] == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and default_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0F1_PIP_AUDIT_REMEDIATION_PLAN",
        "mode": "audit_and_plan_only_no_dependency_change",
        "ok": ok,
        "decision": "S0F1_PLAN_READY" if ok and vuln_count else "S0F1_NO_VULNERABILITY_OR_REVIEW_REQUIRED",
        "pip_audit_available": audit["available"],
        "pip_audit_command": audit["command"],
        "pip_audit_returncode": audit["returncode"],
        "vulnerability_count": vuln_count,
        "vulnerable_package_count": len(packages_with_vulns),
        "packages_with_vulnerabilities": packages_with_vulns,
        "by_package": dict(by_package),
        "by_fix_status": dict(by_has_fix),
        "no_fix_count": no_fix_count,
        "findings": findings,
        "upgrade_groups": groups,
        "generated_apply_script": str(APPLY_PS1),
        "requirement_files": requirement_files,
        "freeze_returncode": freeze_result["returncode"],
        "pip_list_returncode": pip_list_result["returncode"],
        "compileall_returncode": compile_result["returncode"],
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": quality_summary,
        "pytest_default_returncode": default_pytest["returncode"],
        "pytest_default_summary": default_summary,
        "s0a_rerun": s0a_rerun,
        "next_action": "S0F2 Wave1 runtime paket güncellemesi uygulanabilir." if ok and groups.get("wave1_runtime_priority") else "S0F2 için manuel paket kararı gerekebilir.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 S0F1 Pip-Audit Remediation Plan",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Pip-audit available: {result['pip_audit_available']}",
        f"- Pip-audit returncode: {result['pip_audit_returncode']}",
        f"- Vulnerability count: {result['vulnerability_count']}",
        f"- Vulnerable package count: {result['vulnerable_package_count']}",
        f"- No-fix count: {result['no_fix_count']}",
        f"- Generated apply script: `{result['generated_apply_script']}`",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        f"- Pytest default returncode: {result['pytest_default_returncode']}",
        "",
        "## Packages With Vulnerabilities",
        "",
        "```json",
        json.dumps(packages_with_vulns, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Upgrade Groups",
        "",
        "```json",
        json.dumps(groups, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Findings",
        "",
        "```json",
        json.dumps(findings, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Requirement Files",
        "",
        "```json",
        json.dumps(requirement_files, ensure_ascii=False, indent=2),
        "```",
        "",
        "## S0A Rerun",
        "",
        "```json",
        json.dumps(s0a_rerun, ensure_ascii=False, indent=2),
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

    print("S0F1_REPORT_JSON:", OUT_JSON)
    print("S0F1_REPORT_MD:", OUT_MD)
    print("S0F1_APPLY_PS1:", APPLY_PS1)
    print("S0F1_PIP_AUDIT_AVAILABLE:", result["pip_audit_available"])
    print("S0F1_PIP_AUDIT_RETURN_CODE:", result["pip_audit_returncode"])
    print("S0F1_VULNERABILITY_COUNT:", result["vulnerability_count"])
    print("S0F1_VULNERABLE_PACKAGE_COUNT:", result["vulnerable_package_count"])
    print("S0F1_PACKAGES_WITH_VULNS:", json.dumps(packages_with_vulns, ensure_ascii=False))
    print("S0F1_BY_PACKAGE:", json.dumps(dict(by_package), ensure_ascii=False))
    print("S0F1_BY_FIX_STATUS:", json.dumps(dict(by_has_fix), ensure_ascii=False))
    print("S0F1_UPGRADE_GROUPS:", json.dumps(groups, ensure_ascii=False))
    print("S0F1_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("S0F1_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("S0F1_PYTEST_DEFAULT_RETURN_CODE:", result["pytest_default_returncode"])
    print("S0F1_PYTEST_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("S0F1_S0A_PIP_AUDIT_VULNERABILITY_COUNT:", s0a_rerun.get("pip_audit_vulnerability_count"))
    print("S0F1_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
