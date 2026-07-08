#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import zipfile
from pathlib import PurePosixPath, Path
from typing import Any

PACKAGE = "BYS360_RELEASE_ZIP_PREFLIGHT_V1"

BLOCKED_DIRS_ANYWHERE = {".git", ".venv", "venv", "env", "__pycache__", "logs", "instance", "backups", "backup"}
BLOCKED_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".dump", ".log", ".bak", ".backup", ".jks", ".keystore", ".p12", ".pfx", ".pem", ".key"}
TEXT_SUFFIXES = {".py", ".txt", ".md", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".ps1", ".bat", ".sh", ".html", ".css", ".js", ".dart", ".properties"}
SECRET_PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |)?PRIVATE KEY-----")),
    ("jwt_like", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("secret_assignment", re.compile(r"(?m)^\s*(DATABASE_URL|DB_PASSWORD|PASSWORD|SECRET_KEY|TOKEN|API_KEY)\s*=\s*([^\s#'\"]{12,})")),
]
PLACEHOLDER_OK = ("example", "placeholder", "change_me", "changeme", "dummy", "sample", "your_", "not_real", "buraya", "<", "***")


def is_blocked_name(name: str) -> str | None:
    p = PurePosixPath(name)
    parts = set(p.parts)
    base = p.name
    blocked_parts = parts & BLOCKED_DIRS_ANYWHERE
    if blocked_parts:
        return f"yasaklı klasör: {sorted(blocked_parts)[0]}"
    if base.startswith(".env"):
        return ".env dosyası release içinde olamaz"
    if p.suffix.lower() in BLOCKED_SUFFIXES:
        return f"yasaklı dosya uzantısı: {p.suffix}"
    return None


def scan_text(name: str, text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for label, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0)
            low = value.lower()
            if any(token in low for token in PLACEHOLDER_OK):
                continue
            line = text.count("\n", 0, match.start()) + 1
            findings.append({"type": label, "path": name, "line": line, "preview": value[:120]})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, dest="zip_path")
    parser.add_argument("--output-dir", default="reports/security/release_zip_preflight_v1")
    args = parser.parse_args()

    zip_path = Path(args.zip_path).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "package": PACKAGE,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "zip": str(zip_path),
        "status": "PASS",
        "blockers": [],
        "warnings": [],
        "counts": {},
    }

    if not zip_path.exists():
        report["status"] = "FAIL"
        report["blockers"].append({"type": "missing_zip", "message": f"Zip bulunamadı: {zip_path}"})
    else:
        with zipfile.ZipFile(zip_path, "r") as zf:
            infos = zf.infolist()
            report["counts"] = {"files": len(infos), "zip_size_bytes": zip_path.stat().st_size}
            for info in infos:
                name = info.filename
                reason = is_blocked_name(name)
                if reason:
                    report["blockers"].append({"type": "blocked_path", "path": name, "reason": reason})
                    continue
                if info.file_size > 1_500_000:
                    continue
                suffix = PurePosixPath(name).suffix.lower()
                if suffix not in TEXT_SUFFIXES and PurePosixPath(name).name not in {"requirements.txt", "Dockerfile"}:
                    continue
                try:
                    text = zf.read(info).decode("utf-8", errors="ignore")
                except Exception as exc:
                    report["warnings"].append({"type": "read_error", "path": name, "message": str(exc)})
                    continue
                report["blockers"].extend(scan_text(name, text))

    if report["blockers"]:
        report["status"] = "FAIL"

    json_path = out_dir / "BYS360_RELEASE_ZIP_PREFLIGHT_V1_REPORT.json"
    md_path = out_dir / "BYS360_RELEASE_ZIP_PREFLIGHT_V1_REPORT.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [f"# {PACKAGE} Raporu", "", f"- Durum: **{report['status']}**", f"- Zip: `{zip_path}`", f"- Blocker: {len(report['blockers'])}", f"- Uyarı: {len(report['warnings'])}", ""]
    if report["blockers"]:
        lines.append("## Blocker Bulgular")
        for item in report["blockers"][:100]:
            path = item.get("path", "-")
            reason = item.get("reason") or item.get("type") or item.get("message")
            line = item.get("line")
            suffix = f":{line}" if line else ""
            lines.append(f"- `{path}{suffix}` — {reason}")
        if len(report["blockers"]) > 100:
            lines.append(f"- ... {len(report['blockers']) - 100} bulgu daha var.")
    else:
        lines.append("## Sonuç")
        lines.append("Release zipi .env, .git, log, veritabanı ve imzalama anahtarı açısından temiz görünüyor.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "blockers": len(report["blockers"]), "reports": {"json": str(json_path), "md": str(md_path)}}, ensure_ascii=False, indent=2))
    return 1 if report["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
