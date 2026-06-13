# -*- coding: utf-8 -*-
"""Gate for BYS360 Secure Release & Script Handover V1.3."""
from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path

OK = "BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_3_GATE_OK"
FAIL = "BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_3_GATE_FAIL"
WARN = "BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_3_GATE_WARN"

DENY_CONTENT_PATTERNS = [
    ("sentry_placeholder_env", re.compile(r"SENTRY_DSN\s*=\s*https://\.\.\.", re.IGNORECASE)),
    ("hardcoded_123456_password_assignment", re.compile(r"(initial_password\s*=\s*[\"']123456[\"']|set_password\(\s*[\"']123456[\"']\s*\))", re.IGNORECASE)),
]

SKIP_SCAN_PREFIXES = (
    "scripts/security/check_bys360_secure_release_secret_clean_",
    "scripts/security/build_bys360_secure_release_",
    "scripts/security/repair_bys360_secure_release_secret_clean_",
    "docs/security/",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def check_required_files(project: Path) -> list[str]:
    req = [
        "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.ps1",
        "scripts/security/repair_bys360_secure_release_secret_clean_v1_3.py",
        "scripts/security/check_bys360_secure_release_secret_clean_v1_3.ps1",
        "scripts/security/check_bys360_secure_release_secret_clean_v1_3.py",
        "scripts/security/build_bys360_secure_release_v1_3.py",
        "scripts/windows/build_bys360_secure_release_v1_3.ps1",
        "docs/handover/SCRIPTS_DEVIR_TESLIM_NOTU.md",
        "docs/deploy/ENV_TEMPLATE.md",
        "scripts/README.md",
    ]
    return [f"zorunlu dosya eksik: {r}" for r in req if not (project / r).exists()]


def scan_source(project: Path) -> list[str]:
    errors: list[str] = []
    for path in project.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(project).as_posix()
        lower = rel.lower()
        if any(lower.startswith(prefix.lower()) for prefix in SKIP_SCAN_PREFIXES):
            continue
        if any(part in lower for part in ["/.git/", "/.venv/", "/__pycache__/", "/dist_secure/"]):
            continue
        if path.suffix.lower() not in {".py", ".ps1", ".html", ".js", ".css", ".md", ".txt", ".env", ".example", ""}:
            continue
        text = read_text(path)
        for label, pattern in DENY_CONTENT_PATTERNS:
            if pattern.search(text):
                errors.append(f"{rel} içinde yasaklı kalıntı bulundu: {label}")
    return errors


def check_env_files(project: Path) -> list[str]:
    errors: list[str] = []
    env_example = project / ".env.example"
    if env_example.exists():
        text = read_text(env_example)
        if "SENTRY_DSN=https" in text:
            errors.append(".env.example içinde gerçek/placeholder SENTRY_DSN URL görünmemeli; boş tutulmalı.")
        if "PASSWORD@" not in text:
            errors.append(".env.example güvenli şablon formatında görünmüyor; repair V1.3 çalıştırılmalı.")
    gi = project / ".gitignore"
    if not gi.exists() or "# BYS360 secure release / secret hygiene" not in read_text(gi):
        errors.append(".gitignore güvenli dışlama bloğu eksik; repair V1.3 çalıştırılmalı.")
    return errors


def check_latest_release(project: Path) -> list[str]:
    dist = project / "dist_secure"
    if not dist.exists():
        return []
    zips = sorted(dist.glob("BYS360_SECURE_RELEASE_V1_3_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not zips:
        return []
    latest = zips[0]
    errors: list[str] = []
    with zipfile.ZipFile(latest, "r") as zf:
        names = zf.namelist()
        for name in names:
            lower = name.lower()
            if lower == ".env" or lower.startswith(".env") or lower.endswith(".env.example") or "/.env" in lower:
                errors.append(f"son release içinde env dosyası var: {name}")
            if "repair_bys360_secure_release_secret_clean_v1_1" in lower or "repair_bys360_secure_release_secret_clean_v1_2" in lower:
                errors.append(f"son release içinde eski versioned güvenlik scripti var: {name}")
    return errors


def script_inventory_warning(project: Path) -> list[str]:
    scripts = list((project / "scripts").rglob("*.ps1")) + list((project / "scripts").rglob("*.py"))
    if len(scripts) > 120:
        return [f"UYARI: scripts klasöründe {len(scripts)} script var; kaynakta kalabilir ama devir paketinde V1.3 release profili eski overlay scriptlerini dışlar."]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    project = Path(args.project_root).resolve()

    errors: list[str] = []
    errors.extend(check_required_files(project))
    errors.extend(check_env_files(project))
    errors.extend(scan_source(project))
    errors.extend(check_latest_release(project))

    warnings = script_inventory_warning(project)

    if errors:
        print(FAIL)
        for err in errors:
            print(f" - {err}")
        for w in warnings:
            print(f" - {w}")
        return 1

    print(OK)
    for w in warnings:
        print(f" - {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
