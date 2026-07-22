from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SECRET_NAMES = {".env", ".env.local", ".env.production", ".flaskenv"}
SECRET_SUFFIXES = (".key", ".pem", ".p12", ".pfx", ".ppk", ".jks", ".keystore")
SKIP_DIRS = {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def _is_secret(path: Path) -> bool:
    name = path.name.lower()
    if name in SECRET_NAMES:
        return True
    if name.startswith(".env.") and not name.endswith(".example"):
        return True
    return name.endswith(SECRET_SUFFIXES)


def main() -> int:
    findings: list[str] = []
    for path in PROJECT_ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and _is_secret(path):
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            findings.append(rel)
    payload = {"project_root": str(PROJECT_ROOT), "secret_like_files": findings, "count": len(findings)}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if findings:
        print("HATA: Proje/paylaşım paketi içinde gizli dosya benzeri kayıtlar var. Paylaşmadan önce temizleyin.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
