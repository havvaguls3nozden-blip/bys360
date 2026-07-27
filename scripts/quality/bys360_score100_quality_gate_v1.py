#!/usr/bin/env python3
"""
BYS360 SCORE 100 QUALITY GATE V1

CONTEXT (2026-07-27, canonicalization): this is now the canonical, real
implementation at its intended active path. It previously lived only at
scripts/archive/pre_handover_20260708/quality/bys360_score100_quality_gate_v1.py
and was reached through a runpy.run_path() delegating shim at this path (see
commit 4f41319, "chore: archive inactive handover scripts and clean repo
noise", and the later Campaign 1B shim commit that restored the broken
reference). The archived copy is left untouched as a historical snapshot;
this file is the one .github/workflows/bys360-score100-quality-gate-v1.yml
and scripts/windows/repair_bys360_score100_quality_gate_v1.ps1 now run
directly, with no archive dependency.

Amaç:
- Maintenance/BYS360 saha raporunda puan kırdıran kritik kalite ve güvenlik başlıklarını
  tek komutla ölçmek.
- Varsayılan modda projeyi değiştirmemek.
- fix-safe modunda yalnızca düşük riskli, geri alınabilir düzeltmeleri yapmak.

Bu betik bilinçli olarak üçüncü parti paket zorunluluğu içermez. ruff, pip-audit,
pytest gibi araçlar varsa çalıştırır; yoksa bunu rapora uyarı olarak yazar.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, TypedDict, cast

PACKAGE = "BYS360_SCORE_100_QUALITY_GATE_V1"
VERSION = "1.0.0"

DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "htmlcov",
    "coverage",
    "releases",
    "backups",
    "archive",
    "logs",
    "reports",
}

TEXT_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".ps1",
    ".bat",
    ".sh",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".dart",
    ".properties",
    ".env",
    ".example",
}

KNOWN_REPORT_FLAGGED_PINS = {
    "flask": "3.0.3",
    "python-dotenv": "1.0.1",
    "waitress": "3.0.0",
    "pillow": "10.4.0",
    "cryptography": "46.0.4",
}

SECRET_PATTERNS = [
    ("password_literal", re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key)\b\s*[:=]\s*['\"]?([^'\"\s#]{8,})")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("generic_private_key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |)?PRIVATE KEY-----")),
    ("jwt_like", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]

PLACEHOLDER_WORDS = (
    "placeholder",
    "change_me",
    "changeme",
    "example",
    "dummy",
    "sample",
    "your_",
    "local_only",
    "buraya",
    "xxxx",
    "todo",
    "not_real",
)


@dataclass
class Finding:
    check_id: str
    title: str
    severity: str  # FAIL, WARN, PASS, INFO
    message: str
    path: str | None = None
    line: int | None = None
    evidence: Any = None
    recommendation: str | None = None


@dataclass
class GateReport:
    package: str
    version: str
    generated_at: str
    project_root: str
    mode: str
    status: str = "PASS"
    score_estimate: int = 100
    counts: dict[str, int] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    # BYS360 Phase 6 dependency-audit closure (2026-07-27): explicit,
    # machine-readable dependency-audit outcome, additive to the existing
    # Finding-based PIP_AUDIT/PIP_AUDIT_UNAVAILABLE findings below (those are
    # kept unchanged for backward compatibility with existing score/status
    # consumers). Populated only when --run-pip-audit was requested; see
    # classify_dependency_audit_result().
    dependency_audit: dict[str, Any] = field(default_factory=dict)

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)


def relpath(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def safe_read_text(path: Path, max_bytes: int = 2_000_000) -> str | None:
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def iter_files(root: Path, include_reports: bool = False) -> Iterable[Path]:
    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS)
    if include_reports:
        exclude_dirs.discard("reports")
    for current, dirs, files in os.walk(root):
        cur = Path(current)
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".tox")]
        for name in files:
            path = cur / name
            yield path


def is_text_candidate(path: Path) -> bool:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name.startswith(".env"):
        return True
    if suffix in TEXT_EXTENSIONS:
        return True
    return name in {"requirements.txt", "constraints.txt", "dockerfile", "makefile"}


def load_allowlist(project_root: Path, explicit: Path | None) -> dict[str, Any]:
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.extend(
        [
            project_root / "config" / "quality" / "score100_quality_gate_v1_allowlist.json",
            project_root / "config" / "quality" / "score100_allowlist.json",
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                return {}
    return {}

def _load_score100_quality_baseline_v1e(root: Path) -> dict[str, Any]:
    """Load legacy debt baselines for the senior regression gate."""
    path = root / "config" / "quality" / "score100_quality_gate_baseline_v1e.json"
    defaults = {"broad_except_count": 2012, "ruff_total": 7592, "ruff_f821": 0, "ruff_f403": 0}
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                defaults.update({k: data[k] for k in defaults if k in data})
    except Exception:
        pass
    return defaults

def run_cmd(cmd: list[str], cwd: Path, timeout: int = 120, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            timeout=timeout,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            env=merged_env,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired as exc:
        return 124, cast(str, exc.stdout or ""), cast(str, exc.stderr or f"Timeout after {timeout}s")


def parse_requirements(requirements_path: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    text = safe_read_text(requirements_path) or ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Remove comments after requirement line.
        if " #" in line:
            line = line.split(" #", 1)[0].strip()
        m = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[[^\]]+\])?==([^;\s]+)", line)
        if m:
            pins[m.group(1).lower().replace("_", "-")] = m.group(2)
    return pins


# BYS360 Phase 6 dependency-audit closure (2026-07-27): pip-audit's own
# unreachable-network / DNS / proxy / certificate failures must be reported
# as BLOCKED, not silently folded into the same generic "unavailable" bucket
# as a real audit error. These substrings are matched case-insensitively
# against the combined stdout+stderr of the pip-audit subprocess.
_DEPENDENCY_AUDIT_NETWORK_BLOCKED_MARKERS = (
    "connectionerror",
    "failed to establish a new connection",
    "getaddrinfo failed",
    "name or service not known",
    "newconnectionerror",
    "max retries exceeded",
    "proxyerror",
    "sslerror",
    "temporary failure in name resolution",
    "readtimeout",
    "connecttimeout",
    "certificate verify failed",
    "network is unreachable",
    "no route to host",
    "nodename nor servname provided",
)


def classify_dependency_audit_result(
    *,
    return_code: int,
    stdout: str,
    stderr: str,
    audit_json_path: Path,
    duration_seconds: float,
) -> tuple[str, str, int | None, int | None]:
    """Classify a completed pip-audit subprocess run into PASS/FAIL/BLOCKED.

    Returns (status, reason, packages_scanned, vulnerabilities_found).
    ``status`` is always exactly one of "PASS", "FAIL", "BLOCKED" -- never a
    fourth bucket -- so callers can enforce policy without guessing.

    This function does not itself run anything or touch the network; it only
    interprets an already-completed subprocess result, which is what makes
    it deterministically unit-testable (see
    tests/quality/test_score100_dependency_audit_status_contract.py).
    """
    combined_lower = f"{stdout}\n{stderr}".lower()

    if return_code == 124:
        return "BLOCKED", "timeout", None, None

    if return_code == 127 or "modulenotfounderror" in combined_lower and "pip_audit" in combined_lower:
        return "BLOCKED", "tool_not_available", None, None

    if any(marker in combined_lower for marker in _DEPENDENCY_AUDIT_NETWORK_BLOCKED_MARKERS):
        return "BLOCKED", "network_unreachable", None, None

    if return_code == 0:
        packages_scanned, vulnerabilities = _read_pip_audit_json_summary(audit_json_path)
        return "PASS", "clean_scan", packages_scanned, vulnerabilities

    if return_code == 1 and audit_json_path.exists():
        packages_scanned, vulnerabilities = _read_pip_audit_json_summary(audit_json_path)
        if vulnerabilities:
            return "FAIL", "vulnerabilities_found", packages_scanned, vulnerabilities
        return "FAIL", "audit_error_undetermined", packages_scanned, vulnerabilities

    return "FAIL", "audit_error_undetermined", None, None


def _read_pip_audit_json_summary(audit_json_path: Path) -> tuple[int | None, int | None]:
    """Best-effort parse of pip-audit's JSON output for a packages/vulns
    summary. Never raises -- an unexpected schema degrades to (None, None)
    rather than crashing the gate."""
    try:
        data = json.loads(audit_json_path.read_text(encoding="utf-8"))
    except Exception:
        return None, None
    dependencies = data.get("dependencies") if isinstance(data, dict) else None
    if not isinstance(dependencies, list):
        return None, None
    packages_scanned = len(dependencies)
    vulnerabilities = 0
    for dep in dependencies:
        if isinstance(dep, dict) and isinstance(dep.get("vulns"), list):
            vulnerabilities += len(dep["vulns"])
    return packages_scanned, vulnerabilities


def resolve_dependency_audit_policy(explicit: str | None) -> str:
    """Strict|Diagnostic policy resolution. Explicit CLI value always wins;
    otherwise a real CI signal (``CI=true``, the standard GitHub Actions
    default) selects Strict, and anything else (a local/dev run) selects
    Diagnostic. Never guesses -- absence of the CI signal is treated as
    "not CI", matching GitHub Actions' own documented default."""
    if explicit:
        normalized = explicit.strip().lower()
        if normalized in {"strict", "diagnostic"}:
            return normalized
    ci_signal = (os.environ.get("CI") or "").strip().lower()
    return "strict" if ci_signal == "true" else "diagnostic"


def check_dependency_pins(
    root: Path,
    report: GateReport,
    run_pip_audit: bool,
    dependency_audit_python: str | None = None,
) -> None:
    req = root / "requirements.txt"
    if not req.exists():
        report.add(
            Finding(
                "DEPENDENCY_REQUIREMENTS_MISSING",
                "requirements.txt bulunamadı",
                "WARN",
                "Bağımlılık kapısı requirements.txt üzerinden çalışamadı.",
                recommendation="Projenin ana bağımlılık dosyasını kökte tutun veya gate komutuna özel dosya desteği ekleyin.",
            )
        )
        return

    pins = parse_requirements(req)
    flagged = []
    for pkg, version in KNOWN_REPORT_FLAGGED_PINS.items():
        if pins.get(pkg) == version:
            flagged.append({"package": pkg, "version": version})
    if flagged:
        report.add(
            Finding(
                "DEPENDENCY_REPORT_FLAGGED_PINS",
                "Saha raporunda CVE riskiyle işaretlenen bağımlılık pinleri duruyor",
                "FAIL",
                "requirements.txt içinde saha raporunda riskli listelenen paket sürümleri bulundu.",
                path="requirements.txt",
                evidence=flagged,
                recommendation="Önce pip-audit çalıştırın; sonra Flask, python-dotenv, waitress, Pillow ve cryptography için güncel güvenli sürümlere yükseltin. Sürüm seçimini pip-audit çıktısına göre yapın.",
            )
        )
    else:
        report.add(
            Finding(
                "DEPENDENCY_REPORT_FLAGGED_PINS",
                "Saha raporunda işaretlenen eski bağımlılık pinleri görünmüyor",
                "PASS",
                "requirements.txt, rapordaki riskli pinlerle birebir eşleşmiyor.",
                path="requirements.txt",
            )
        )

    if run_pip_audit:
        out_dir = Path(report.artifacts.get("output_dir", root / "reports" / "quality"))
        out_dir.mkdir(parents=True, exist_ok=True)
        audit_json = out_dir / "score100_pip_audit_v1.json"
        audit_python = dependency_audit_python or sys.executable
        cmd = [audit_python, "-m", "pip_audit", "-r", str(req), "-f", "json", "-o", str(audit_json)]
        audit_started = _dt.datetime.now()
        rc, stdout, stderr = run_cmd(cmd, root, timeout=240)
        duration_seconds = (_dt.datetime.now() - audit_started).total_seconds()

        audit_status, audit_reason, packages_scanned, vulnerabilities = classify_dependency_audit_result(
            return_code=rc,
            stdout=stdout,
            stderr=stderr,
            audit_json_path=audit_json,
            duration_seconds=duration_seconds,
        )
        report.dependency_audit = {
            "dependency_audit_status": audit_status,
            "dependency_audit_reason": audit_reason,
            "dependency_audit_exit_code": rc,
            "dependency_audit_duration_seconds": round(duration_seconds, 3),
            "dependency_audit_tool": "pip-audit",
            "dependency_audit_python": audit_python,
            "dependency_audit_target_manifest": relpath(req, root),
            "dependency_audit_packages_scanned": packages_scanned,
            "dependency_audit_vulnerabilities": vulnerabilities,
        }

        if audit_status == "PASS":
            report.add(
                Finding(
                    "PIP_AUDIT",
                    "pip-audit yeşil",
                    "PASS",
                    "pip-audit requirements.txt için bilinen açık döndürmedi.",
                    evidence={"output": relpath(audit_json, root)},
                )
            )
        elif audit_status == "FAIL" and audit_reason == "vulnerabilities_found":
            report.add(
                Finding(
                    "PIP_AUDIT",
                    "pip-audit açık buldu",
                    "FAIL",
                    "pip-audit requirements.txt için güvenlik açığı raporladı.",
                    evidence={"output": relpath(audit_json, root), "stderr_tail": stderr[-2000:]},
                    recommendation="pip-audit JSON çıktısındaki fix_versions alanlarına göre bağımlılıkları yükseltin.",
                )
            )
        elif audit_status == "FAIL":
            report.add(
                Finding(
                    "PIP_AUDIT_FAILED",
                    "pip-audit gerçek tarama hatasıyla sonuçlandı",
                    "FAIL",
                    "pip-audit ağ/timeout dışı bir nedenle başarısız oldu; sonuç güvenilir bir PASS değil.",
                    evidence={"returncode": rc, "reason": audit_reason, "stdout_tail": stdout[-2000:], "stderr_tail": stderr[-2000:]},
                    recommendation="pip-audit çıktısını inceleyin; requirements.txt veya ortam çözümleme hatası olabilir.",
                )
            )
        else:
            # BLOCKED: network/DNS/proxy/certificate/timeout/tool-missing.
            # Kept as a WARN Finding (not FAIL) for backward compatibility
            # with the existing score/status computation -- the explicit
            # dependency_audit_status above is what downstream consumers and
            # the Strict CI policy actually key off of, not this Finding.
            report.add(
                Finding(
                    "PIP_AUDIT_UNAVAILABLE",
                    "pip-audit çalıştırılamadı",
                    "WARN",
                    "pip-audit ortamsal bir nedenle (ağ/timeout/araç eksikliği) tamamlanamadı; bu bir PASS kanıtı değildir.",
                    evidence={"returncode": rc, "reason": audit_reason, "stdout_tail": stdout[-2000:], "stderr_tail": stderr[-2000:]},
                    recommendation=".venv içinde pip install pip-audit komutunu çalıştırın veya ağ/proxy erişimini doğrulayın.",
                )
            )


def redact_android_key_example(path: Path) -> bool:
    text = safe_read_text(path) or ""
    if not text:
        return False
    backup = path.with_suffix(path.suffix + ".score100_v1.bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    lines = []
    changed = False
    for raw in text.splitlines():
        if raw.strip().startswith("storePassword="):
            lines.append("storePassword=CHANGE_ME_LOCAL_ONLY")
            changed = True
        elif raw.strip().startswith("keyPassword="):
            lines.append("keyPassword=CHANGE_ME_LOCAL_ONLY")
            changed = True
        elif raw.strip().startswith("storeFile="):
            lines.append("storeFile=../keystores/CHANGE_ME_RELEASE_KEYSTORE.jks")
            changed = True
        else:
            lines.append(raw)
    new_text = "\n".join(lines) + "\n"
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return changed
    return False


def looks_like_placeholder(value: str) -> bool:
    lower = value.strip().strip("'\"").lower()
    return any(word in lower for word in PLACEHOLDER_WORDS)


def check_android_signing(root: Path, report: GateReport, fix_safe: bool) -> None:
    matches = list(dict.fromkeys(list(root.glob("**/android/key.properties.example")) + list(root.glob("**/key.properties.example"))))
    if not matches:
        report.add(
            Finding(
                "ANDROID_SIGNING_EXAMPLE_MISSING",
                "Android imzalama örnek dosyası bulunamadı",
                "INFO",
                "key.properties.example dosyası taramada bulunmadı. Mobil proje yoksa normaldir.",
            )
        )
        return

    for path in matches:
        text = safe_read_text(path) or ""
        suspicious: list[dict[str, str]] = []
        for line in text.splitlines():
            if "=" not in line or line.strip().startswith("#"):
                continue
            key, value = [part.strip() for part in line.split("=", 1)]
            if key.lower() in {"storepassword", "keypassword"} and value and not looks_like_placeholder(value):
                suspicious.append({"key": key, "value_preview": value[:3] + "***"})
        if suspicious:
            if fix_safe:
                changed = redact_android_key_example(path)
                report.add(
                    Finding(
                        "ANDROID_SIGNING_EXAMPLE_SECRET_FIXED",
                        "Android örnek imzalama parolası placeholder yapıldı",
                        "PASS" if changed else "WARN",
                        "fix-safe modunda key.properties.example içindeki parola alanları yerel placeholder değere çevrildi.",
                        path=relpath(path, root),
                        evidence={"backup": relpath(path.with_suffix(path.suffix + ".score100_v1.bak"), root)},
                        recommendation="Gerçek üretim parolası sızmış olma ihtimali varsa release keystore/store parolalarını ayrıca döndürün.",
                    )
                )
            else:
                report.add(
                    Finding(
                        "ANDROID_SIGNING_EXAMPLE_SECRET",
                        "Android imzalama parolası örnek dosyada gerçek değer gibi duruyor",
                        "FAIL",
                        "key.properties.example içinde placeholder olmayan storePassword/keyPassword değerleri bulundu.",
                        path=relpath(path, root),
                        evidence=suspicious,
                        recommendation="fix-safe modunu çalıştırın veya dosyayı elle placeholder değerlerle güncelleyin. Gerçek parola buysa keystore/store parolalarını değiştirin.",
                    )
                )
        else:
            report.add(
                Finding(
                    "ANDROID_SIGNING_EXAMPLE_SECRET",
                    "Android imzalama örnek dosyası placeholder görünüyor",
                    "PASS",
                    "key.properties.example içinde gerçek parola gibi görünen değer bulunmadı.",
                    path=relpath(path, root),
                )
            )


def check_git_tracked_env(root: Path, report: GateReport) -> None:
    rc, stdout, stderr = run_cmd(["git", "ls-files"], root, timeout=30)
    if rc != 0:
        env_files = [relpath(p, root) for p in root.glob(".env*") if p.is_file()]
        if env_files:
            report.add(
                Finding(
                    "ENV_FILES_PRESENT_NO_GIT_CHECK",
                    ".env dosyaları var, git takip durumu doğrulanamadı",
                    "WARN",
                    "Yerel geliştirme için .env bulunabilir; ancak release paketine girmemeli ve git tarafından takip edilmemeli.",
                    evidence=env_files,
                    recommendation="git ls-files .env* ile takip edilmediğini doğrulayın; release paketinde .env bulunmamalı.",
                )
            )
        return
    tracked = [line.strip() for line in stdout.splitlines() if line.strip()]
    bad = [p for p in tracked if Path(p).name.startswith(".env") and not p.endswith(".example")]
    if bad:
        report.add(
            Finding(
                "ENV_TRACKED_BY_GIT",
                ".env dosyası git tarafından takip ediliyor",
                "FAIL",
                "Gerçek ortam dosyaları kaynak kontrolünde görünmemeli.",
                evidence=bad,
                recommendation=".env dosyasını git takibinden çıkarın, geçmişte secret sızıntısı varsa secret rotation yapın ve release paketlerinden temizleyin.",
            )
        )
    else:
        report.add(
            Finding(
                "ENV_TRACKED_BY_GIT",
                ".env git takibinde görünmüyor",
                "PASS",
                "git ls-files çıktısında .env/.env.production gibi gerçek ortam dosyası takipli görünmedi.",
            )
        )


def check_secret_patterns(root: Path, report: GateReport, allowlist: dict[str, Any]) -> None:
    allowed_paths = set(allowlist.get("secret_scan_allowed_paths", []))
    findings: list[dict[str, Any]] = []
    scan_names = {".env", ".env.production", ".env.local", "key.properties", "key.properties.example"}
    for path in iter_files(root):
        rp = relpath(path, root)
        if rp in allowed_paths:
            continue
        name = path.name.lower()
        if not (name in scan_names or name.startswith(".env") or path.suffix.lower() in {".properties", ".yml", ".yaml", ".json", ".toml", ".ini"}):
            continue
        text = safe_read_text(path, max_bytes=500_000)
        if text is None:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for label, pattern in SECRET_PATTERNS:
                m = pattern.search(line)
                if not m:
                    continue
                preview = line[:140]
                if any(word in preview.lower() for word in PLACEHOLDER_WORDS):
                    continue
                findings.append({"path": rp, "line": i, "pattern": label, "preview": preview})
                break
            if len(findings) >= 50:
                break
    if findings:
        report.add(
            Finding(
                "SECRET_PATTERN_SCAN",
                "Secret benzeri değerler bulundu",
                "WARN",
                "Bu bulgular otomatik kesin hüküm değildir; ancak release öncesi tek tek incelenmelidir.",
                evidence=findings[:50],
                recommendation="Gerçek secret ise dosyadan çıkarın, .env/local secret store kullanın ve gerekirse parolayı/tokenı döndürün.",
            )
        )
    else:
        report.add(
            Finding(
                "SECRET_PATTERN_SCAN",
                "Secret pattern taraması temiz",
                "PASS",
                "Taranan konfigürasyon dosyalarında bariz secret pattern bulunmadı.",
            )
        )


def check_tckn_encryption(root: Path, report: GateReport) -> None:
    config_hits: list[dict[str, Any]] = []
    usage_hits: list[dict[str, Any]] = []
    test_hits: list[dict[str, Any]] = []
    model_storage_hits: list[dict[str, Any]] = []

    def _hit(rp: str, line_no: int, line: str) -> dict[str, Any]:
        return {"path": rp, "line": line_no, "preview": line.strip()[:180]}

    storage_pattern = re.compile(r"(?i)(tckn|tc_kimlik|kimlik_no)")

    for path in iter_files(root):
        if path.suffix.lower() != ".py":
            continue

        rp = relpath(path, root)
        text = safe_read_text(path)
        if not text:
            continue

        lines = text.splitlines()

        for line_no, line in enumerate(lines, 1):
            if "TCKN_ENCRYPTION_KEY" in line:
                config_hits.append(_hit(rp, line_no, line))

            if rp == "app/security/tckn_crypto.py" and any(
                marker in line
                for marker in (
                    "def encrypt_tckn",
                    "def decrypt_tckn",
                    "def mask_tckn",
                    "def is_encrypted_tckn",
                )
            ):
                usage_hits.append(_hit(rp, line_no, line))

            if rp.startswith("app/models/") and storage_pattern.search(line):
                model_storage_hits.append(_hit(rp, line_no, line))

        if rp.startswith("tests/") and all(
            marker in text
            for marker in (
                "encrypt_tckn",
                "decrypt_tckn",
                "mask_tckn",
                "plaintext not in token",
                "is_encrypted_tckn",
            )
        ):
            test_hits.append(
                {
                    "path": rp,
                    "line": 1,
                    "preview": "TCKN token plaintext dışlama, decrypt roundtrip ve maskeleme sözleşmesi",
                }
            )

    evidence = {
        "config_hits": config_hits[:12],
        "usage_hits": usage_hits[:12],
        "test_hits": test_hits[:12],
        "model_storage_hits": model_storage_hits[:12],
    }

    if config_hits and usage_hits and test_hits and not model_storage_hits:
        report.add(
            Finding(
                "TCKN_ENCRYPTION_CONFIG_WITH_USAGE",
                "TCKN şifreleme helper ve test sözleşmesi doğrulandı",
                "PASS",
                "TCKN anahtarı, şifreleme/çözme/maskeleme helper'ı ve plaintext dışlama testi mevcut; model katmanında açık TCKN alanı görünmedi.",
                evidence=evidence,
                recommendation="Canlı ortamda TCKN_ENCRYPTION_KEY güçlü secret olarak tanımlı kalmalı; ileride model alanı eklenirse DB storage testi de eklenmelidir.",
            )
        )
    elif config_hits or usage_hits:
        report.add(
            Finding(
                "TCKN_ENCRYPTION_CONFIG_WITH_USAGE",
                "TCKN şifreleme kullanımı için aday kod bulundu",
                "WARN",
                "Anahtar veya encrypt/decrypt benzeri kullanım var; test/model kanıtı tamamlanmalı.",
                evidence=evidence,
                recommendation="Unit test ekleyin: düz TCKN değeri token/DB içinde açık kalmamalı; maskeleme ve yetkili çözümleme kuralı doğrulanmalı.",
            )
        )
    else:
        report.add(
            Finding(
                "TCKN_ENCRYPTION_CONFIG_WITH_USAGE",
                "TCKN şifreleme kullanımı görünmüyor",
                "PASS",
                "TCKN saklama/şifreleme akışı repo içinde aktif görünmüyor.",
            )
        )


def check_exec_routes(root: Path, report: GateReport) -> None:
    """Classify builtin exec()/compile() calls by runtime risk.

    Regex literals such as re.compile(...) are expected and should not trigger
    this gate. Contract-protected legacy mobile bridge calls and tooling/test
    compile checks are reported as INFO; unreviewed runtime app usage remains WARN.
    """
    legacy_mobile_bridge_paths = {
        "app/api/mobile/communication_read_routes.py",
        "app/api/mobile/communication_v2_read_routes.py",
        "app/api/mobile/detail_read_routes.py",
        "app/api/mobile/light_read_routes.py",
        "app/api/mobile/performance_read_routes.py",
        "app/api/mobile/support_survey_read_routes.py",
        "app/api/mobile/utility_routes.py",
    }

    runtime_hits: list[dict[str, Any]] = []
    reviewed_hits: list[dict[str, Any]] = []
    tooling_hits: list[dict[str, Any]] = []

    for path in iter_files(root):
        if path.suffix.lower() != ".py":
            continue

        text = safe_read_text(path)
        if not text or ("exec(" not in text and "compile(" not in text):
            continue

        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue

        rp = relpath(path, root)
        lines = text.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name):
                continue
            if node.func.id not in {"exec", "compile"}:
                continue

            line_no = getattr(node, "lineno", 0) or 0
            preview = lines[line_no - 1].strip()[:180] if 0 < line_no <= len(lines) else node.func.id
            hit = {"path": rp, "line": line_no, "preview": preview}

            if rp in legacy_mobile_bridge_paths and node.func.id == "exec":
                reviewed_hits.append(hit)
            elif rp.startswith("scripts/") or rp.startswith("tests/"):
                tooling_hits.append(hit)
            else:
                runtime_hits.append(hit)

    if runtime_hits:
        report.add(
            Finding(
                "PYTHON_EXEC_COMPILE_USAGE",
                "İncelenmemiş runtime exec()/compile() kullanımı bulundu",
                "WARN",
                "Uygulama runtime kodunda dinamik kod yürütme lint, test ve IDE görünürlüğünü zayıflatır.",
                evidence=runtime_hits[:50],
                recommendation="Runtime app kodundaki exec/compile kullanımını normal Python modülüne taşıyın veya gerekçeli allowlist ekleyin.",
            )
        )
    else:
        report.add(
            Finding(
                "PYTHON_EXEC_COMPILE_USAGE",
                "İncelenmemiş runtime exec()/compile() kullanımı bulunmadı",
                "PASS",
                "Regex compile, test/tooling compile ve sözleşme testiyle korunan legacy bridge kullanımları runtime risk uyarısından ayrıştırıldı.",
            )
        )

    if reviewed_hits or tooling_hits:
        report.add(
            Finding(
                "PYTHON_EXEC_COMPILE_REVIEWED_USAGE",
                "Gerekçeli exec()/compile() kullanımları raporlandı",
                "INFO",
                "Legacy mobil bridge ve kalite/test amaçlı compile kullanımları görünür tutuldu; genel runtime WARN kapsamına alınmadı.",
                evidence={
                    "legacy_mobile_bridge": reviewed_hits[:20],
                    "tooling_or_tests": tooling_hits[:20],
                },
                recommendation="Mobil bridge kaldırılacaksa route contract snapshot güncellenmeden ve endpoint davranışı doğrulanmadan commit etmeyin.",
            )
        )


def check_duplicate_endpoint_test_skip(root: Path, report: GateReport) -> None:
    """Verify the duplicate endpoint pytest is active.

    V1C2: scan only real test files. Older gate logic scanned helper scripts too;
    strings inside V1A/V1B/V1C maintenance scripts triggered a false
    DUPLICATE_ENDPOINT_TEST_SKIPPED finding.
    """
    target_name = "test_app_factory_registers_routes_without_duplicate_endpoints"
    found: list[dict[str, object]] = []
    skip_context: list[dict[str, object]] = []
    test_roots = ((root / "tests"),)

    for test_root in test_roots:
        if not test_root.exists():
            continue
        for path in test_root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            text = safe_read_text(path)
            if not text or target_name not in text:
                continue
            rp = relpath(path, root)
            lines = text.splitlines()
            for i, line in enumerate(lines, 1):
                if target_name not in line:
                    continue
                found.append({"path": rp, "line": i})
                ctx = "\n".join(lines[max(0, i - 10): min(len(lines), i + 20)])
                ctx_lower = ctx.lower()
                if (
                    "pytest.mark.skip" in ctx_lower
                    or "pytest.mark.skipif" in ctx_lower
                    or "pytest.skip(" in ctx_lower
                    or "os.environ" in ctx
                    or "os.getenv" in ctx
                    or "getenv(" in ctx
                ):
                    skip_context.append({"path": rp, "line": i, "context": ctx[:1000]})

    if not found:
        report.add(
            Finding(
                "DUPLICATE_ENDPOINT_TEST_MISSING",
                "Çift endpoint testi bulunamadı",
                "FAIL",
                "tests altında test_app_factory_registers_routes_without_duplicate_endpoints testi bulunamadı.",
                recommendation="tests/quality/test_app_factory_registers_routes_without_duplicate_endpoints.py dosyasını varsayılan CI koşusunda zorunlu hale getirin.",
            )
        )
    elif skip_context:
        report.add(
            Finding(
                "DUPLICATE_ENDPOINT_TEST_SKIPPED",
                "Çift endpoint testi koşullu/skip görünüyor",
                "FAIL",
                "Duplicate endpoint testi özel ortam değişkeni veya skip koşulu arkasında görünüyor.",
                evidence=skip_context[:5],
                recommendation="Bu testi varsayılan CI koşusunda zorunlu hale getirin; yalnızca gerekçeli allowlist üzerinden istisna kabul edin.",
            )
        )
    else:
        report.add(
            Finding(
                "DUPLICATE_ENDPOINT_TEST_ACTIVE",
                "Çift endpoint testi aktif görünüyor",
                "PASS",
                "Duplicate endpoint testi tests altında bulundu ve skip/env koşulu arkasında görünmüyor.",
                evidence=found[:5],
            )
        )


def check_app_factory_duplicate_rules(root: Path, report: GateReport, enabled: bool, strict: bool) -> None:
    if not enabled:
        report.add(
            Finding(
                "APP_FACTORY_DUPLICATE_RULE_CHECK_SKIPPED",
                "App factory duplicate route kontrolü atlandı",
                "INFO",
                "Bu kontrolü çalıştırmak için -RunAppFactoryDuplicateCheck parametresini kullanın.",
            )
        )
        return
    env = {
        "BYS360_QUALITY_GATE": "1",
        "FLASK_ENV": "testing",
        "APP_ENV": "testing",
        "DATABASE_URL": os.environ.get("DATABASE_URL", "sqlite:///:memory:"),
        "WTF_CSRF_ENABLED": "false",
    }
    code = r'''
import json
from collections import Counter, defaultdict
from app import create_app
app = create_app()
rows = []
for rule in app.url_map.iter_rules():
    methods = tuple(sorted(m for m in rule.methods if m not in {'HEAD', 'OPTIONS'}))
    rows.append({'endpoint': rule.endpoint, 'rule': str(rule), 'methods': methods})
key_counts = Counter((r['endpoint'], r['rule'], tuple(r['methods'])) for r in rows)
dups = [
    {'endpoint': k[0], 'rule': k[1], 'methods': list(k[2]), 'count': v}
    for k, v in key_counts.items()
    if v > 1
]
print(json.dumps({'rules': len(rows), 'duplicates': dups}, ensure_ascii=False))
'''
    rc, stdout, stderr = run_cmd([sys.executable, "-c", code], root, timeout=180, env=env)
    if rc != 0:
        report.add(
            Finding(
                "APP_FACTORY_DUPLICATE_RULE_CHECK_FAILED_TO_RUN",
                "App factory route kontrolü çalıştırılamadı",
                "FAIL" if strict else "WARN",
                "create_app() test ortamında açılırken hata aldı.",
                evidence={"returncode": rc, "stdout_tail": stdout[-2000:], "stderr_tail": stderr[-4000:]},
                recommendation="Local test env değişkenlerini tamamlayın. Gate için app factory açılabilmelidir.",
            )
        )
        return
    try:
        data = json.loads(stdout.strip().splitlines()[-1])
    except Exception:
        report.add(
            Finding(
                "APP_FACTORY_DUPLICATE_RULE_PARSE_ERROR",
                "App factory route çıktısı okunamadı",
                "WARN",
                "Kontrol çalıştı fakat JSON çıktı parse edilemedi.",
                evidence={"stdout_tail": stdout[-4000:], "stderr_tail": stderr[-1000:]},
            )
        )
        return
    dups = data.get("duplicates") or []
    if dups:
        report.add(
            Finding(
                "APP_FACTORY_DUPLICATE_RULES",
                "Flask URL map içinde çift route kaydı bulundu",
                "FAIL",
                "Aynı endpoint + path + method kombinasyonu birden fazla kayıtlı görünüyor.",
                evidence={"rules": data.get("rules"), "duplicates": dups[:100]},
                recommendation="Tekrarlayan blueprint/register çağrılarını kaldırın veya istisna ise allowlist ve test gerekçesi ekleyin.",
            )
        )
    else:
        report.add(
            Finding(
                "APP_FACTORY_DUPLICATE_RULES",
                "Flask URL map çift route kontrolü temiz",
                "PASS",
                "Aynı endpoint + path + method kombinasyonu tekrar etmiyor.",
                evidence={"rules": data.get("rules", 0)},
            )
        )


def check_wildcard_imports(root: Path, report: GateReport) -> None:
    hits: list[dict[str, Any]] = []
    parse_errors = 0
    for path in iter_files(root):
        if path.suffix.lower() != ".py":
            continue
        text = safe_read_text(path)
        if not text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            parse_errors += 1
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
                hits.append({"path": relpath(path, root), "line": getattr(node, "lineno", None), "module": node.module})
    if hits:
        report.add(
            Finding(
                "WILDCARD_IMPORTS",
                "Wildcard import bulundu",
                "FAIL",
                "from x import * kullanımı sürdürülebilirlik ve F821 riskini artırır.",
                evidence=hits[:100],
                recommendation="Wildcard importları açık isimli importlara çevirin.",
            )
        )
    else:
        report.add(
            Finding(
                "WILDCARD_IMPORTS",
                "Wildcard import bulunmadı",
                "PASS",
                "Python AST taramasında wildcard import görünmedi.",
                evidence={"parse_errors": parse_errors},
            )
        )


def check_broad_except(root: Path, report: GateReport) -> None:
    hits = []
    for path in iter_files(root):
        if path.suffix.lower() != ".py":
            continue
        text = safe_read_text(path)
        if not text:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"except\s+Exception\s*:", line) or re.search(r"except\s*:", line):
                hits.append({"path": relpath(path, root), "line": i, "preview": line.strip()})
    if hits:
        baseline = _load_score100_quality_baseline_v1e(root)
        broad_baseline = int(baseline.get("broad_except_count", 2012) or 2012)
        sev = "PASS" if len(hits) <= broad_baseline else "FAIL"
        report.add(
            Finding(
                "BROAD_EXCEPT_COUNT",
                "Geniş except blokları bulundu",
                sev,
                f"Toplam {len(hits)} adet except Exception / bare except pattern'i bulundu.",
                evidence={"count": len(hits), "sample": hits[:50]},
                recommendation="Sessiz hata yutma yerine spesifik exception yakalayın ve log/geri bildirim standardını uygulayın.",
            )
        )
    else:
        report.add(
            Finding(
                "BROAD_EXCEPT_COUNT",
                "Geniş except pattern'i bulunmadı",
                "PASS",
                "except Exception / bare except taraması temiz.",
            )
        )


def run_ruff(root: Path, report: GateReport, enabled: bool) -> None:
    if not enabled:
        return
    target = "app" if (root / "app").exists() else "."
    rc, stdout, stderr = run_cmd([sys.executable, "-m", "ruff", "check", target, "--output-format=json"], root, timeout=240)
    if rc == 0:
        report.add(
            Finding("RUFF_CHECK", "ruff temiz", "PASS", f"ruff check {target} bulgu döndürmedi.")
        )
        return
    if rc in {1, 2}:
        count = 0
        f821 = 0
        wildcard = 0
        try:
            data = json.loads(stdout or "[]")
            count = len(data)
            for item in data:
                if item.get("code") == "F821":
                    f821 += 1
                if item.get("code") == "F403":
                    wildcard += 1
        except Exception:
            pass
        baseline = _load_score100_quality_baseline_v1e(root)
        ruff_total_baseline = int(baseline.get("ruff_total", 7592) or 7592)
        ruff_f821_baseline = int(baseline.get("ruff_f821", 0) or 0)
        ruff_f403_baseline = int(baseline.get("ruff_f403", 0) or 0)
        severity = "PASS" if f821 <= ruff_f821_baseline and wildcard <= ruff_f403_baseline and count <= ruff_total_baseline else "FAIL"
        report.add(
            Finding(
                "RUFF_CHECK",
                "ruff bulguları var",
                severity,
                f"ruff check {target} toplam {count or 'bilinmeyen'} bulgu döndürdü. F821={f821}, F403={wildcard}.",
                evidence={"returncode": rc, "count": count, "F821": f821, "F403": wildcard, "stderr_tail": stderr[-2000:]},
                recommendation="Önce F821 ve wildcard importları sıfırlayın; sonra ruff backlog'u paket paket azaltın.",
            )
        )
    else:
        report.add(
            Finding(
                "RUFF_CHECK_UNAVAILABLE",
                "ruff çalıştırılamadı",
                "WARN",
                "ruff kurulu değil veya hata aldı.",
                evidence={"returncode": rc, "stdout_tail": stdout[-2000:], "stderr_tail": stderr[-2000:]},
                recommendation=".venv içinde pip install ruff veya pyproject/requirements kurulumunu doğrulayın.",
            )
        )


class _LargeFileEntry(TypedDict):
    path: str
    size_kb: float


def check_repo_shape(root: Path, report: GateReport) -> None:
    counts: dict[str, int] = {
        "py_files": 0,
        "jinja_templates": 0,
        "css_files": 0,
        "js_files": 0,
        "md_files": 0,
        "scripts_files": 0,
        "active_script_files": 0,
        "active_md_files": 0,
        "governance_script_files": 0,
        "governance_md_files": 0,
    }
    large_files: list[_LargeFileEntry] = []
    script_buckets: dict[str, int] = {}
    md_buckets: dict[str, int] = {}

    governance_script_prefixes = (
        "scripts/quality/",
        "scripts/windows/",
    )
    governance_md_prefixes = (
        "docs/quality/",
        "docs/architecture/",
        "docs/security/",
        "docs/qa/",
        "docs/technical_debt/",
        "docs/handover/",
        "docs/portal/",
        "reports/",
    )

    def _bucket(rp: str, depth: int = 2) -> str:
        parts = rp.split("/")
        return "/".join(parts[:depth]) if len(parts) >= depth else rp

    for path in iter_files(root):
        suffix = path.suffix.lower()
        rp = relpath(path, root)
        if suffix == ".py":
            counts["py_files"] += 1
        if suffix in {".html", ".jinja", ".j2"} and ("templates/" in rp or "template" in rp.lower()):
            counts["jinja_templates"] += 1
        if suffix == ".css":
            counts["css_files"] += 1
        if suffix == ".js":
            counts["js_files"] += 1
        if suffix == ".md":
            counts["md_files"] += 1
            bucket = _bucket(rp, 2) if rp.startswith(("docs/", "reports/")) else _bucket(rp, 1)
            md_buckets[bucket] = md_buckets.get(bucket, 0) + 1
            if rp.startswith(governance_md_prefixes):
                counts["governance_md_files"] += 1
            else:
                counts["active_md_files"] += 1
        if rp.startswith("scripts/"):
            counts["scripts_files"] += 1
            bucket = _bucket(rp, 2)
            script_buckets[bucket] = script_buckets.get(bucket, 0) + 1
            if rp.startswith(governance_script_prefixes):
                counts["governance_script_files"] += 1
            else:
                counts["active_script_files"] += 1
        try:
            size = path.stat().st_size
        except Exception:
            size = 0
        if suffix in {".py", ".js", ".css", ".html"} and size > 250_000:
            large_files.append({"path": rp, "size_kb": round(size / 1024, 1)})

    report.counts.update(counts)

    script_buckets_top = dict(sorted(script_buckets.items(), key=lambda item: item[1], reverse=True)[:15])
    md_buckets_top = dict(sorted(md_buckets.items(), key=lambda item: item[1], reverse=True)[:15])

    if large_files:
        report.add(
            Finding(
                "LARGE_SOURCE_FILES",
                "Devasa kaynak dosyaları var",
                "WARN",
                "Bakım maliyeti yüksek dosyalar tespit edildi.",
                evidence=sorted(large_files, key=lambda x: x["size_kb"], reverse=True)[:30],
                recommendation="Devasa dosyaları alan bazlı modüllere bölün; özellikle JS/Python route dosyalarını küçük servis dosyalarına ayırın.",
            )
        )

    active_script_limit = 250
    active_md_limit = 150
    evidence = {
        "totals": {
            "scripts_files": counts["scripts_files"],
            "md_files": counts["md_files"],
        },
        "active": {
            "active_script_files": counts["active_script_files"],
            "active_md_files": counts["active_md_files"],
            "active_script_limit": active_script_limit,
            "active_md_limit": active_md_limit,
        },
        "governance_or_evidence": {
            "governance_script_files": counts["governance_script_files"],
            "governance_md_files": counts["governance_md_files"],
        },
        "script_buckets_top": script_buckets_top,
        "md_buckets_top": md_buckets_top,
    }

    if counts["active_script_files"] > active_script_limit or counts["active_md_files"] > active_md_limit:
        report.add(
            Finding(
                "REPO_SCRIPT_DOC_BLOAT",
                "Aktif script/doküman kalabalığı yüksek",
                "WARN",
                "Aktif bakım yüzeyindeki script veya doküman sayısı eşik üstünde görünüyor.",
                evidence=evidence,
                recommendation="Tek seferlik scriptleri arşive taşıyın; kalıcı kalite kontrollerini merkezi gate altında toplayın.",
            )
        )
    elif counts["scripts_files"] > 250 or counts["md_files"] > 150:
        report.add(
            Finding(
                "REPO_SCRIPT_DOC_BLOAT",
                "Script/doküman envanteri yapılandırılmış görünüyor",
                "INFO",
                "Toplam sayı yüksek olsa da aktif bakım yüzeyi eşik altında; yük kalite/dokümantasyon kanıtı olarak sınıflandırıldı.",
                evidence=evidence,
                recommendation="Yeni tek seferlik SAFE/HOTFIX üretimini artırmayın; kalite ve canlı hazırlık kanıtlarını merkezi rapor düzeninde tutun.",
            )
        )

    report.add(
        Finding(
            "REPO_SHAPE_SUMMARY",
            "Repo şekil özeti üretildi",
            "INFO",
            "Kaynak dosya sayıları rapora eklendi.",
            evidence=counts,
        )
    )


def maybe_update_gitignore(root: Path, report: GateReport, fix_safe: bool) -> None:
    if not fix_safe:
        return
    gitignore = root / ".gitignore"
    additions = [
        "",
        "# BYS360 SCORE 100 QUALITY GATE V1 - local secrets",
        ".env",
        ".env.local",
        ".env.production",
        "mobile_flutter/**/android/key.properties",
        "mobile_flutter/**/android/*.jks",
        "mobile_flutter/**/android/*.keystore",
    ]
    existing = safe_read_text(gitignore) or ""
    missing = [line for line in additions if line and line not in existing]
    if missing:
        backup = gitignore.with_suffix(gitignore.suffix + ".score100_v1.bak")
        if gitignore.exists() and not backup.exists():
            shutil.copy2(gitignore, backup)
        with gitignore.open("a", encoding="utf-8") as fh:
            fh.write("\n" + "\n".join(additions) + "\n")
        report.add(
            Finding(
                "GITIGNORE_SECRET_RULES_ADDED",
                ".gitignore secret kuralları eklendi",
                "PASS",
                "fix-safe modunda yerel secret ve Android imza dosyaları .gitignore içine eklendi.",
                path=".gitignore",
                evidence={"added": missing, "backup": relpath(backup, root) if backup.exists() else None},
            )
        )


def write_report(report: GateReport, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    report.artifacts["output_dir"] = str(output_dir)
    json_path = output_dir / "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json"
    md_path = output_dir / "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.md"
    data = asdict(report)
    # dataclasses nested asdict converts findings.
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    fail_count = sum(1 for f in report.findings if f.severity == "FAIL")
    warn_count = sum(1 for f in report.findings if f.severity == "WARN")
    pass_count = sum(1 for f in report.findings if f.severity == "PASS")

    lines = []
    lines.append(f"# {PACKAGE} Raporu")
    lines.append("")
    lines.append(f"- Durum: **{report.status}**")
    lines.append(f"- Tahmini kalite puanı: **{report.score_estimate}/100**")
    lines.append(f"- Üretim zamanı: `{report.generated_at}`")
    lines.append(f"- Proje kökü: `{report.project_root}`")
    lines.append(f"- Mod: `{report.mode}`")
    lines.append(f"- Bulgu sayısı: FAIL={fail_count}, WARN={warn_count}, PASS={pass_count}")
    lines.append("")
    if report.counts:
        lines.append("## Repo Özeti")
        lines.append("")
        for key, value in report.counts.items():
            lines.append(f"- `{key}`: {value}")
        lines.append("")
    lines.append("## Bulgular")
    lines.append("")
    order = {"FAIL": 0, "WARN": 1, "INFO": 2, "PASS": 3}
    for f in sorted(report.findings, key=lambda x: (order.get(x.severity, 9), x.check_id)):
        loc = ""
        if f.path:
            loc = f" — `{f.path}`"
            if f.line:
                loc += f":{f.line}"
        lines.append(f"### [{f.severity}] {f.title}{loc}")
        lines.append("")
        lines.append(f"**Kontrol:** `{f.check_id}`")
        lines.append("")
        lines.append(f.message)
        lines.append("")
        if f.evidence is not None:
            evidence = json.dumps(f.evidence, ensure_ascii=False, indent=2)
            if len(evidence) > 5000:
                evidence = evidence[:5000] + "\n... (kısaltıldı)"
            lines.append("**Kanıt:**")
            lines.append("")
            lines.append("```json")
            lines.append(evidence)
            lines.append("```")
            lines.append("")
        if f.recommendation:
            lines.append(f"**Öneri:** {f.recommendation}")
            lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    report.artifacts["json_report"] = str(json_path)
    report.artifacts["markdown_report"] = str(md_path)


def finalize_score_and_status(report: GateReport, strict: bool) -> None:
    fail_count = sum(1 for f in report.findings if f.severity == "FAIL")
    warn_count = sum(1 for f in report.findings if f.severity == "WARN")

    # Weighted estimate: critical FAILs reduce quickly, warnings reduce slowly.
    score = 100 - min(65, fail_count * 8) - min(20, warn_count * 2)
    # Critical named checks are especially important.
    critical_ids = {
        "DEPENDENCY_REPORT_FLAGGED_PINS",
        "PIP_AUDIT",
        "ANDROID_SIGNING_EXAMPLE_SECRET",
        "TCKN_ENCRYPTION_CONFIG_WITHOUT_USAGE",
        "DUPLICATE_ENDPOINT_TEST_MISSING",
        "DUPLICATE_ENDPOINT_TEST_SKIPPED",
        "APP_FACTORY_DUPLICATE_RULES",
        "ENV_TRACKED_BY_GIT",
    }
    critical_fails = [f for f in report.findings if f.severity == "FAIL" and f.check_id in critical_ids]
    if critical_fails:
        score = min(score, 74)
    elif fail_count:
        score = min(score, 88)
    elif warn_count:
        score = min(score, 96)
    report.score_estimate = max(0, int(score))

    if fail_count:
        report.status = "FAIL"
    elif strict and warn_count:
        report.status = "WARN"
    else:
        report.status = "PASS"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=PACKAGE)
    parser.add_argument("--project-root", default=".", help="BYS360 proje kökü")
    parser.add_argument("--mode", choices=["audit", "fix-safe", "gate"], default="audit")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--allowlist", default=None)
    parser.add_argument("--run-pip-audit", action="store_true")
    parser.add_argument("--run-ruff", action="store_true")
    parser.add_argument("--run-app-factory-duplicate-check", action="store_true")
    parser.add_argument("--strict", action="store_true", help="WARN durumlarını gate modunda daha katı değerlendir")
    parser.add_argument(
        "--dependency-audit-policy",
        choices=["strict", "diagnostic"],
        default=None,
        help=(
            "pip-audit BLOCKED/FAIL sonucunun gate exit code'unu nasıl etkileyeceği. "
            "Belirtilmezse CI=true ise strict, değilse diagnostic varsayılır."
        ),
    )
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"ProjectRoot bulunamadı: {root}", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir).resolve() if args.output_dir else (root / "reports" / "quality" / "score100_quality_gate_v1")
    output_dir.mkdir(parents=True, exist_ok=True)

    report = GateReport(
        package=PACKAGE,
        version=VERSION,
        generated_at=_dt.datetime.now().isoformat(timespec="seconds"),
        project_root=str(root),
        mode=args.mode,
        artifacts={"output_dir": str(output_dir)},
    )

    allowlist = load_allowlist(root, Path(args.allowlist).resolve() if args.allowlist else None)
    fix_safe = args.mode == "fix-safe"

    maybe_update_gitignore(root, report, fix_safe=fix_safe)
    check_dependency_pins(root, report, run_pip_audit=args.run_pip_audit)
    check_android_signing(root, report, fix_safe=fix_safe)
    check_git_tracked_env(root, report)
    check_secret_patterns(root, report, allowlist=allowlist)
    check_tckn_encryption(root, report)
    check_duplicate_endpoint_test_skip(root, report)
    check_app_factory_duplicate_rules(root, report, enabled=args.run_app_factory_duplicate_check, strict=args.strict or args.mode == "gate")
    check_exec_routes(root, report)
    check_wildcard_imports(root, report)
    check_broad_except(root, report)
    run_ruff(root, report, enabled=args.run_ruff)
    check_repo_shape(root, report)

    finalize_score_and_status(report, strict=args.strict)
    write_report(report, output_dir)

    dependency_audit_policy = resolve_dependency_audit_policy(args.dependency_audit_policy)
    print(f"DEPENDENCY_AUDIT_POLICY={dependency_audit_policy}")

    summary = {
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "status": report.status,
        "score_estimate": report.score_estimate,
        "findings": {
            "FAIL": sum(1 for f in report.findings if f.severity == "FAIL"),
            "WARN": sum(1 for f in report.findings if f.severity == "WARN"),
            "PASS": sum(1 for f in report.findings if f.severity == "PASS"),
            "INFO": sum(1 for f in report.findings if f.severity == "INFO"),
        },
        "dependency_audit_policy": dependency_audit_policy,
        "dependency_audit": report.dependency_audit or None,
        "reports": {
            "json": str(output_dir / "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json"),
            "md": str(output_dir / "BYS360_SCORE100_QUALITY_GATE_V1_REPORT.md"),
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.mode == "gate" and report.status == "FAIL":
        return 1
    if args.mode == "gate" and args.strict and report.status != "PASS":
        return 1
    # BYS360 Phase 6 dependency-audit closure (2026-07-27): in Strict policy
    # (real CI), a BLOCKED or FAIL dependency-audit result must fail the gate
    # even if no other Finding pushed report.status to FAIL -- a network
    # limitation or undetected audit error must never present as green in CI.
    # In Diagnostic policy (local/dev), BLOCKED stays a non-fatal WARN signal
    # (already reflected in report.status/score_estimate above); it is never
    # silently upgraded to a hard pass or a hard fail here.
    dependency_status = report.dependency_audit.get("dependency_audit_status") if report.dependency_audit else None
    if args.mode == "gate" and dependency_audit_policy == "strict" and dependency_status in {"FAIL", "BLOCKED"}:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
