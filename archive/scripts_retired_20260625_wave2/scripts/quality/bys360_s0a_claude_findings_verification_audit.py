from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import json
import os
import re
import shutil
import subprocess
import sys

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"

OUT_JSON = QUALITY / "BYS360_S0A_MAINTENANCE_FINDINGS_VERIFICATION_AUDIT.json"
OUT_MD = QUALITY / "BYS360_S0A_MAINTENANCE_FINDINGS_VERIFICATION_AUDIT.md"

SECRET_TERMS = [
    "SECRET_KEY",
    "TCKN_ENCRYPTION_KEY",
    "DATABASE_URL",
    "DB_PASSWORD",
    "POSTGRES_PASSWORD",
    "MAIL_PASSWORD",
    "MAIL_USERNAME",
    "SENTRY_DSN",
    "INSTAGRAM_ACCESS_TOKEN",
    "FLASK_SECRET",
]

EXCLUDE_DIRS_FOR_SECRET_SCAN = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "reports",
    "logs",
    "releases",
    "archive",
    "backups",
}

TEXT_SUFFIXES_FOR_SECRET_SCAN = {
    ".py",
    ".txt",
    ".md",
    ".env",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".ps1",
    ".bat",
    ".cmd",
    ".sh",
}


def run_cmd(cmd, timeout=300):
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="ignore",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=timeout,
        )
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-20000:],
        }
    except FileNotFoundError as exc:
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
            "combined_tail": str(exc),
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
            "combined_tail": (stdout + "\n" + stderr + "\nTIMEOUT")[-20000:],
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


def size_bytes(path: Path) -> int:
    if not path.exists():
        return 0

    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0

    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            pass
    return total


def mb(value: int) -> float:
    return round(value / 1024 / 1024, 2)


def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""


def check_config_exc_bug() -> dict:
    path = ROOT / "config.py"
    text = read_text_safe(path)

    findings = []

    if path.exists():
        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            if "exc_info=exc" not in line:
                continue

            window_start = max(1, idx - 12)
            window = lines[window_start - 1:idx]
            joined = "\n".join(window)

            has_except_exception_plain = bool(re.search(r"except\s+Exception\s*:", joined))
            has_except_exception_as_exc = bool(re.search(r"except\s+Exception\s+as\s+exc\s*:", joined))

            findings.append({
                "path": "config.py",
                "line_no": idx,
                "pattern": "exc_info=exc",
                "plain_except_exception_nearby": has_except_exception_plain,
                "except_exception_as_exc_nearby": has_except_exception_as_exc,
                "risk": "HIGH" if has_except_exception_plain and not has_except_exception_as_exc else "REVIEW",
                "note": "Satır içeriği rapora yazılmadı; sadece pattern doğrulandı.",
            })

    return {
        "checked": path.exists(),
        "path": "config.py",
        "finding_count": len(findings),
        "findings": findings,
        "bug_likely": any(
            item["plain_except_exception_nearby"] and not item["except_exception_as_exc_nearby"]
            for item in findings
        ),
    }


def check_pytest_config_conflict() -> dict:
    pytest_ini = ROOT / "pytest.ini"
    pyproject = ROOT / "pyproject.toml"

    pyproject_text = read_text_safe(pyproject)
    pytest_ini_text = read_text_safe(pytest_ini)

    has_pytest_ini = pytest_ini.exists()
    has_pyproject_pytest = "[tool.pytest.ini_options]" in pyproject_text

    ignored_pyproject_risk = has_pytest_ini and has_pyproject_pytest

    pytest_ini_addopts = []
    if pytest_ini_text:
        for line in pytest_ini_text.splitlines():
            if "addopts" in line or "testpaths" in line or "markers" in line:
                pytest_ini_addopts.append(line.strip())

    pyproject_pytest_lines = []
    if pyproject_text and has_pyproject_pytest:
        capture = False
        for line in pyproject_text.splitlines():
            if line.strip() == "[tool.pytest.ini_options]":
                capture = True
                pyproject_pytest_lines.append(line.strip())
                continue
            if capture and line.strip().startswith("[") and line.strip() != "[tool.pytest.ini_options]":
                break
            if capture:
                clean = line.strip()
                if clean:
                    pyproject_pytest_lines.append(clean)

    return {
        "pytest_ini_exists": has_pytest_ini,
        "pyproject_exists": pyproject.exists(),
        "pyproject_has_tool_pytest_ini_options": has_pyproject_pytest,
        "conflict_likely": ignored_pyproject_risk,
        "pytest_ini_relevant_lines": pytest_ini_addopts[:80],
        "pyproject_pytest_relevant_lines": pyproject_pytest_lines[:120],
        "risk": "HIGH" if ignored_pyproject_risk else "OK_OR_REVIEW",
        "note": "pytest.ini varsa pytest genelde pyproject içindeki pytest ayarlarını yok sayar.",
    }


def find_backup_test_dirs() -> dict:
    roots = [
        ROOT / "reports",
        ROOT / "reports" / "quality",
        ROOT / "backups",
        ROOT / "archive",
    ]

    dirs = []

    for root in roots:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_dir():
                continue

            low = str(path).lower()
            if "backup" not in low and "_bak" not in low:
                continue

            tests_dir = path / "tests"
            if tests_dir.exists() and tests_dir.is_dir():
                test_files = list(tests_dir.rglob("test_*.py")) + list(tests_dir.rglob("*_test.py"))
                dirs.append({
                    "path": str(tests_dir.relative_to(ROOT)).replace("\\", "/"),
                    "test_file_count": len(test_files),
                    "size_mb": mb(size_bytes(tests_dir)),
                })

    dirs.sort(key=lambda x: (x["test_file_count"], x["size_mb"]), reverse=True)

    return {
        "backup_test_dir_count": len(dirs),
        "backup_test_file_count": sum(item["test_file_count"] for item in dirs),
        "backup_test_dirs_top_80": dirs[:80],
        "risk": "HIGH" if dirs else "OK",
    }


def find_old_venv_dirs() -> dict:
    candidates = []

    for path in ROOT.iterdir():
        if not path.is_dir():
            continue

        name = path.name.lower()
        if name.startswith(".venv_old") or name.startswith("venv_old") or name.startswith(".venv-backup") or name.startswith("venv-backup"):
            candidates.append({
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "size_mb": mb(size_bytes(path)),
            })

    candidates.sort(key=lambda x: x["size_mb"], reverse=True)

    return {
        "old_venv_dir_count": len(candidates),
        "old_venv_total_mb": round(sum(item["size_mb"] for item in candidates), 2),
        "old_venv_dirs": candidates,
        "risk": "HIGH" if sum(item["size_mb"] for item in candidates) >= 100 else ("REVIEW" if candidates else "OK"),
    }


def find_quality_backup_dirs() -> dict:
    quality = ROOT / "reports" / "quality"
    candidates = []

    if quality.exists():
        for path in quality.rglob("*"):
            if not path.is_dir():
                continue

            low = path.name.lower()
            full = str(path).lower()
            if "backup" in low or "backups" in full or "_bak" in low:
                candidates.append({
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "size_mb": mb(size_bytes(path)),
                })

    candidates.sort(key=lambda x: x["size_mb"], reverse=True)

    return {
        "quality_backup_dir_count": len(candidates),
        "quality_backup_total_mb": round(sum(item["size_mb"] for item in candidates), 2),
        "quality_backup_dirs_top_80": candidates[:80],
        "risk": "REVIEW" if candidates else "OK",
    }


def check_git_secret_history() -> dict:
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        return {
            "git_repo_detected": False,
            "risk": "UNKNOWN",
            "note": ".git klasörü bulunamadı; geçmiş taraması yapılamadı.",
        }

    env_history = run_cmd([
        "git",
        "log",
        "--all",
        "--name-only",
        "--pretty=format:%H",
        "--",
        ".env",
        ".env.*",
        "config/.env",
        "instance/.env",
    ], timeout=120)

    env_history_lines = [
        line.strip()
        for line in (env_history["stdout"] or "").splitlines()
        if line.strip()
    ]

    secret_regex = "(" + "|".join(re.escape(term) for term in SECRET_TERMS) + ")"

    secret_history = run_cmd([
        "git",
        "log",
        "--all",
        "--oneline",
        "-G",
        secret_regex,
        "--",
        ".",
    ], timeout=180)

    secret_history_lines = [
        line.strip()
        for line in (secret_history["stdout"] or "").splitlines()
        if line.strip()
    ]

    return {
        "git_repo_detected": True,
        "env_history_returncode": env_history["returncode"],
        "env_history_hit_count": len(env_history_lines),
        "env_history_hits_top_80": env_history_lines[:80],
        "secret_history_returncode": secret_history["returncode"],
        "secret_history_commit_hit_count": len(secret_history_lines),
        "secret_history_commits_top_80": secret_history_lines[:80],
        "risk": "HIGH" if env_history_lines or secret_history_lines else "OK_OR_REVIEW",
        "note": "Güvenlik için commit diff veya secret değerleri rapora yazılmadı; sadece commit/path sinyali üretildi.",
    }


def should_secret_scan_file(path: Path) -> bool:
    if not path.is_file():
        return False

    parts = set(path.parts)
    if parts & EXCLUDE_DIRS_FOR_SECRET_SCAN:
        return False

    if path.name.lower().startswith(".env"):
        return True

    if path.suffix.lower() in TEXT_SUFFIXES_FOR_SECRET_SCAN:
        return True

    return False


def scan_worktree_secret_terms() -> dict:
    findings = []

    for path in ROOT.rglob("*"):
        if not should_secret_scan_file(path):
            continue

        text = read_text_safe(path)
        if not text:
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            for term in SECRET_TERMS:
                if term in line:
                    findings.append({
                        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "line_no": line_no,
                        "term": term,
                        "note": "Satır değeri rapora yazılmadı.",
                    })

    by_term = Counter(item["term"] for item in findings)
    by_path = Counter(item["path"] for item in findings)

    return {
        "worktree_secret_term_hit_count": len(findings),
        "by_term": dict(by_term),
        "by_path_top_80": dict(by_path.most_common(80)),
        "findings_top_200": findings[:200],
        "risk": "REVIEW" if findings else "OK",
        "note": "Bu tarama değerleri göstermez; sadece dosya/satır/terim bilgisini verir.",
    }


def run_ruff_f821_config_check() -> dict:
    py = ROOT / ".venv" / "Scripts" / "python.exe"

    if not py.exists():
        py = Path(sys.executable)

    cmd = [
        str(py),
        "-m",
        "ruff",
        "check",
        "config.py",
        "--select",
        "F821",
        "--output-format",
        "json",
    ]

    result = run_cmd(cmd, timeout=120)

    findings = []
    try:
        findings = json.loads(result["stdout"] or "[]")
    except Exception:
        findings = []

    return {
        "ruff_command": result["cmd"],
        "returncode": result["returncode"],
        "available": result["returncode"] != 127 and "No module named ruff" not in result["combined_tail"],
        "f821_count": len(findings) if isinstance(findings, list) else None,
        "findings": findings[:80] if isinstance(findings, list) else [],
        "raw_tail": result["combined_tail"][-4000:],
        "risk": "HIGH" if isinstance(findings, list) and findings else ("TOOL_MISSING_OR_REVIEW" if result["returncode"] in {1, 127} and not findings else "OK"),
    }


def run_pip_audit() -> dict:
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    pip_audit_exe = ROOT / ".venv" / "Scripts" / "pip-audit.exe"

    commands = []

    if pip_audit_exe.exists():
        commands.append([str(pip_audit_exe), "--format", "json", "--progress-spinner", "off"])

    if py.exists():
        commands.append([str(py), "-m", "pip_audit", "--format", "json", "--progress-spinner", "off"])

    commands.append(["pip-audit", "--format", "json", "--progress-spinner", "off"])

    selected = None
    result = None

    for cmd in commands:
        candidate = run_cmd(cmd, timeout=300)
        selected = cmd
        result = candidate

        tail = candidate["combined_tail"]
        if candidate["returncode"] in {0, 1} and "No module named pip_audit" not in tail and "not recognized" not in tail:
            break

    if result is None:
        return {"available": False, "risk": "TOOL_MISSING"}

    data = None
    vulnerabilities = []

    try:
        data = json.loads(result["stdout"] or "{}")
    except Exception:
        data = None

    if isinstance(data, dict):
        deps = data.get("dependencies", [])
        for dep in deps:
            name = dep.get("name")
            version = dep.get("version")
            vulns = dep.get("vulns", []) or []
            for vuln in vulns:
                vulnerabilities.append({
                    "package": name,
                    "version": version,
                    "id": vuln.get("id") or vuln.get("aliases", [""])[0],
                    "fix_versions": vuln.get("fix_versions") or vuln.get("fixes") or [],
                })
    elif isinstance(data, list):
        for dep in data:
            name = dep.get("name")
            version = dep.get("version")
            vulns = dep.get("vulns", []) or []
            for vuln in vulns:
                vulnerabilities.append({
                    "package": name,
                    "version": version,
                    "id": vuln.get("id") or vuln.get("aliases", [""])[0],
                    "fix_versions": vuln.get("fix_versions") or vuln.get("fixes") or [],
                })

    by_package = Counter(item["package"] for item in vulnerabilities)

    tool_missing = (
        "No module named pip_audit" in result["combined_tail"]
        or "not recognized" in result["combined_tail"]
        or result["returncode"] == 127
    )

    return {
        "available": not tool_missing,
        "command": " ".join(map(str, selected)) if selected else "",
        "returncode": result["returncode"],
        "vulnerability_count": len(vulnerabilities),
        "by_package": dict(by_package),
        "vulnerabilities_top_120": vulnerabilities[:120],
        "raw_tail": result["combined_tail"][-4000:],
        "risk": "HIGH" if vulnerabilities else ("TOOL_MISSING_OR_REVIEW" if tool_missing else "OK"),
    }


def quick_pytest_quality_smoke() -> dict:
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = Path(sys.executable)

    result = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests/quality",
        "-m",
        "ci_safe",
        "-q",
        "-ra",
    ], timeout=600)

    summary = parse_pytest_summary(result["combined_tail"])

    return {
        "cmd": result["cmd"],
        "returncode": result["returncode"],
        "summary": summary,
        "raw_tail": result["combined_tail"][-6000:],
        "risk": "HIGH" if result["returncode"] != 0 else "OK",
    }


def build_priority_actions(checks: dict) -> list[dict]:
    actions = []

    if checks["git_secret_history"].get("risk") == "HIGH":
        actions.append({
            "priority": 1,
            "title": "Git geçmişinde secret/.env sinyali doğrulandı",
            "action": "Secret değerleri gösterilmeden ilgili commit/path incelenmeli; gerçek sızıntı varsa SECRET_KEY, TCKN_ENCRYPTION_KEY, DB/mail/Sentry anahtarları rotate edilmeli ve geçmiş temizliği planlanmalı.",
            "phase": "S0B",
        })

    if checks["config_exc_bug"].get("bug_likely"):
        actions.append({
            "priority": 2,
            "title": "config.py exc_info=exc bug olasılığı",
            "action": "İlgili except bloğu güvenli hotfix ile `except Exception as exc:` haline getirilmeli ve F821 root kapsamına alınmalı.",
            "phase": "S0C",
        })

    if checks["pytest_config"].get("conflict_likely"):
        actions.append({
            "priority": 3,
            "title": "pytest.ini / pyproject pytest ayar çatışması",
            "action": "Tek pytest konfigürasyon kaynağı seçilmeli; backup test collection dışlanmalı; CI gerçek test koşusuna hazırlanmalı.",
            "phase": "S0D",
        })

    if checks["backup_tests"].get("backup_test_dir_count", 0) > 0:
        actions.append({
            "priority": 4,
            "title": "Backup test klasörleri collection riski oluşturuyor",
            "action": "Silmeden önce arşiv manifesti çıkarılmalı; sonra pytest dışına alınmalı veya archive dışına taşınmalı.",
            "phase": "S0E",
        })

    if checks["pip_audit"].get("vulnerability_count", 0) > 0:
        actions.append({
            "priority": 5,
            "title": "pip-audit zafiyetleri doğrulandı",
            "action": "Paket güncellemeleri küçük dalgalarla yapılmalı; özellikle Waitress/Pillow/cryptography gibi runtime paketleri testli güncellenmeli.",
            "phase": "S0F",
        })

    if checks["old_venvs"].get("old_venv_total_mb", 0) >= 100:
        actions.append({
            "priority": 6,
            "title": "Eski sanal ortam klasörleri proje boyutunu şişiriyor",
            "action": "Önce raporlanmalı, sonra güvenli arşiv/silme scripti ile kaldırılmalı.",
            "phase": "S0G",
        })

    return sorted(actions, key=lambda x: x["priority"])


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)

    checks = {
        "config_exc_bug": check_config_exc_bug(),
        "pytest_config": check_pytest_config_conflict(),
        "backup_tests": find_backup_test_dirs(),
        "old_venvs": find_old_venv_dirs(),
        "quality_backup_dirs": find_quality_backup_dirs(),
        "git_secret_history": check_git_secret_history(),
        "worktree_secret_terms": scan_worktree_secret_terms(),
        "ruff_f821_config": run_ruff_f821_config_check(),
        "pip_audit": run_pip_audit(),
        "pytest_quality_smoke": quick_pytest_quality_smoke(),
    }

    priority_actions = build_priority_actions(checks)

    red_flag_count = len(priority_actions)

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "S0A_MAINTENANCE_FINDINGS_VERIFICATION_AUDIT",
        "mode": "audit_only_no_code_change_no_delete_no_secret_values",
        "ok": True,
        "decision": "S0A_AUDIT_COMPLETED_REVIEW_REQUIRED" if red_flag_count else "S0A_AUDIT_COMPLETED_NO_CRITICAL_FLAGS",
        "red_flag_count": red_flag_count,
        "priority_actions": priority_actions,
        "checks": checks,
        "next_action": "S0B ile en kritik doğrulanmış bulgudan başlanmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 S0A Maintenance Bulguları Doğrulama Audit",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Red flag count: {result['red_flag_count']}",
        "",
        "## Öncelikli Aksiyonlar",
        "",
        "```json",
        json.dumps(priority_actions, ensure_ascii=False, indent=2),
        "```",
        "",
        "## config.py exc Bug Kontrolü",
        "",
        "```json",
        json.dumps(checks["config_exc_bug"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Config Çatışması",
        "",
        "```json",
        json.dumps(checks["pytest_config"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Backup Test Klasörleri",
        "",
        "```json",
        json.dumps(checks["backup_tests"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Eski Sanal Ortam Klasörleri",
        "",
        "```json",
        json.dumps(checks["old_venvs"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Quality Backup Klasörleri",
        "",
        "```json",
        json.dumps(checks["quality_backup_dirs"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Git Secret Geçmiş Sinyali",
        "",
        "```json",
        json.dumps(checks["git_secret_history"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Çalışma Ağacı Secret Terim Sinyali",
        "",
        "```json",
        json.dumps(checks["worktree_secret_terms"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Ruff F821 config.py Kontrolü",
        "",
        "```json",
        json.dumps(checks["ruff_f821_config"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## pip-audit Kontrolü",
        "",
        "```json",
        json.dumps(checks["pip_audit"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Quality Smoke",
        "",
        "```json",
        json.dumps(checks["pytest_quality_smoke"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("S0A_REPORT_JSON:", OUT_JSON)
    print("S0A_REPORT_MD:", OUT_MD)
    print("S0A_DECISION:", result["decision"])
    print("S0A_RED_FLAG_COUNT:", result["red_flag_count"])
    print("S0A_CONFIG_EXC_BUG_LIKELY:", checks["config_exc_bug"].get("bug_likely"))
    print("S0A_PYTEST_CONFIG_CONFLICT_LIKELY:", checks["pytest_config"].get("conflict_likely"))
    print("S0A_BACKUP_TEST_DIR_COUNT:", checks["backup_tests"].get("backup_test_dir_count"))
    print("S0A_BACKUP_TEST_FILE_COUNT:", checks["backup_tests"].get("backup_test_file_count"))
    print("S0A_OLD_VENV_DIR_COUNT:", checks["old_venvs"].get("old_venv_dir_count"))
    print("S0A_OLD_VENV_TOTAL_MB:", checks["old_venvs"].get("old_venv_total_mb"))
    print("S0A_QUALITY_BACKUP_DIR_COUNT:", checks["quality_backup_dirs"].get("quality_backup_dir_count"))
    print("S0A_GIT_SECRET_HISTORY_RISK:", checks["git_secret_history"].get("risk"))
    print("S0A_GIT_ENV_HISTORY_HIT_COUNT:", checks["git_secret_history"].get("env_history_hit_count"))
    print("S0A_GIT_SECRET_COMMIT_HIT_COUNT:", checks["git_secret_history"].get("secret_history_commit_hit_count"))
    print("S0A_WORKTREE_SECRET_TERM_HIT_COUNT:", checks["worktree_secret_terms"].get("worktree_secret_term_hit_count"))
    print("S0A_RUFF_F821_CONFIG_RISK:", checks["ruff_f821_config"].get("risk"))
    print("S0A_RUFF_F821_CONFIG_COUNT:", checks["ruff_f821_config"].get("f821_count"))
    print("S0A_PIP_AUDIT_AVAILABLE:", checks["pip_audit"].get("available"))
    print("S0A_PIP_AUDIT_VULNERABILITY_COUNT:", checks["pip_audit"].get("vulnerability_count"))
    print("S0A_PYTEST_QUALITY_SMOKE_RETURN_CODE:", checks["pytest_quality_smoke"].get("returncode"))
    print("S0A_OK:", result["ok"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
