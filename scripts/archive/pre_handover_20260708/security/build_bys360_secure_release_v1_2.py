from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules", "dist", "dist_secure", "_upload_parts", "uploads", "logs", "log", "instance"
}
EXCLUDED_EXTS = {".pyc", ".pyo", ".zip", ".7z", ".rar", ".log", ".dump", ".db", ".sqlite", ".sqlite3"}
KNOWN_LEAKED_SHA256 = "02837ff7205688e009bd3682a517a7d5ed10e7116ced8725dd97e4eeaf19a631"
HARDCODED_PASSWORD_PATTERNS = [
    re.compile(r'initial_password\s*=\s*["\']123456["\']'),
    re.compile(r'set_password\(\s*["\']123456["\']\s*\)'),
]


def placeholder_url() -> str:
    return "".join(["https://", "...", "@sentry.io", "/..."])


def should_exclude(path: Path, project: Path) -> bool:
    rel = path.relative_to(project)
    if set(rel.parts) & EXCLUDED_DIRS:
        return True
    if path.suffix.lower() in EXCLUDED_EXTS:
        return True
    if path.name.lower().startswith(".env") and path.name != ".env.example":
        return True
    if path.name.lower().endswith((".bak", ".backup")):
        return True
    return False


def contains_known_leak(text: str) -> bool:
    for match in re.finditer(r"[A-Za-z0-9_.!@#$%*\-]{6,64}", text):
        if hashlib.sha256(match.group(0).encode("utf-8")).hexdigest() == KNOWN_LEAKED_SHA256:
            return True
    return False


def verify_member(name: str, data: bytes) -> list[str]:
    errors: list[str] = []
    lower = name.lower()
    if lower == ".env" or lower.startswith(".env."):
        errors.append(f"release içinde env dosyası var: {name}")
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        text = ""
    if text:
        if contains_known_leak(text):
            errors.append(f"release içinde bilinen sızmış parola değeri bulundu: {name}")
        if placeholder_url() in text:
            errors.append(f"release içinde Sentry placeholder URL bulundu: {name}")
        for pat in HARDCODED_PASSWORD_PATTERNS:
            if pat.search(text):
                errors.append(f"release içinde hardcode başlangıç şifresi bulundu: {name}")
    return errors


def build(project: Path) -> Path:
    dist = project / "dist_secure"
    dist.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = dist / f"BYS360_secure_release_v1_2_{stamp}.zip"
    manifest = {
        "name": out.name,
        "created_at": stamp,
        "excluded": sorted(EXCLUDED_DIRS),
        "notes": [".env ve yerel secret dosyaları release dışındadır."],
    }
    errors: list[str] = []
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in project.rglob("*"):
            if not path.is_file() or should_exclude(path, project):
                continue
            rel = path.relative_to(project).as_posix()
            data = path.read_bytes()
            member_errors = verify_member(rel, data)
            if member_errors:
                errors.extend(member_errors)
                continue
            zf.writestr(rel, data)
        zf.writestr("RELEASE_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    if errors:
        out.unlink(missing_ok=True)
        print("BYS360_SECURE_RELEASE_BUILD_V1_2_FAIL")
        for e in errors:
            print(f" - {e}")
        raise SystemExit(1)
    print("BYS360_SECURE_RELEASE_BUILD_V1_2_OK")
    print(str(out))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    build(Path(args.project_root).resolve())


if __name__ == "__main__":
    main()
