from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules", "dist", "dist_secure", "_upload_parts", "uploads", "logs", "log"
}
EXCLUDED_EXTS = {".pyc", ".pyo", ".zip", ".7z", ".rar", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf"}

# Known leaked value is never written as plain text in this checker.
KNOWN_LEAKED_SHA256 = "02837ff7205688e009bd3682a517a7d5ed10e7116ced8725dd97e4eeaf19a631"


def placeholder_url() -> str:
    # Tam placeholder URL bu dosyada düz metin olarak tutulmaz; gate kendini yakalamasın.
    return "".join(["https://", "...", "@sentry.io", "/..."])


HARDCODED_PASSWORD_PATTERNS = [
    re.compile(r'initial_password\s*=\s*["\']123456["\']'),
    re.compile(r'set_password\(\s*["\']123456["\']\s*\)'),
]
SENTRY_PLACEHOLDER_RE = re.compile(r"SENTRY_DSN\s*=\s*https://\.{3}")


def is_excluded(path: Path, project: Path) -> bool:
    rel = path.relative_to(project)
    if set(rel.parts) & EXCLUDED_DIRS:
        return True
    if path.suffix.lower() in EXCLUDED_EXTS:
        return True
    if path.name.lower().startswith(".env") and path.name != ".env.example":
        return True
    return False


def is_secret_tool_file(rel: str) -> bool:
    return (
        rel.startswith("scripts/security/check_bys360_secure_release_secret_clean_")
        or rel.startswith("scripts/security/repair_bys360_secure_release_secret_clean_")
        or rel.startswith("scripts/security/build_bys360_secure_release_")
        or rel.startswith("scripts/windows/build_bys360_secure_release_")
    )


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def contains_known_leak(text: str) -> bool:
    # Basit token taraması: sadece düz metin eşleşmesini hash üzerinden yakalar.
    for match in re.finditer(r"[A-Za-z0-9_.!@#$%*\-]{6,64}", text):
        if hashlib.sha256(match.group(0).encode("utf-8")).hexdigest() == KNOWN_LEAKED_SHA256:
            return True
    return False


def scan_files(project: Path) -> list[str]:
    errors: list[str] = []
    ph = placeholder_url()
    for path in project.rglob("*"):
        if not path.is_file() or is_excluded(path, project):
            continue
        text = read_text(path)
        if text is None:
            continue
        rel = path.relative_to(project).as_posix()
        tool_file = is_secret_tool_file(rel)
        if not tool_file:
            if contains_known_leak(text):
                errors.append(f"{rel} içinde bilinen sızmış parola değeri bulundu")
            if ph in text:
                errors.append(f"{rel} içinde Sentry placeholder URL bulundu")
            if SENTRY_PLACEHOLDER_RE.search(text):
                errors.append(f"{rel} içinde SENTRY_DSN placeholder bulundu")
        for pat in HARDCODED_PASSWORD_PATTERNS:
            if pat.search(text):
                errors.append(f"{rel} içinde hardcode 123456 başlangıç şifresi bulundu")
    return errors


def check_env_example(project: Path) -> list[str]:
    errors: list[str] = []
    p = project / ".env.example"
    if not p.exists():
        return [".env.example bulunamadı"]
    text = p.read_text(encoding="utf-8", errors="ignore")
    ph = placeholder_url()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("SENTRY_DSN="):
            value = stripped.split("=", 1)[1].strip()
            if value and value.lower() not in {"change_me", "changeme"}:
                errors.append(".env.example SENTRY_DSN boş veya CHANGE_ME olmalı; gerçek DSN yazılmamalı")
        if ph in stripped or contains_known_leak(stripped):
            errors.append(".env.example gerçek değer gibi görünen secret içeriyor")
    return errors


def check_gitignore(project: Path) -> list[str]:
    p = project / ".gitignore"
    if not p.exists():
        return [".gitignore bulunamadı"]
    text = p.read_text(encoding="utf-8", errors="ignore")
    needed = [".env", ".env.*", "!.env.example", "dist_secure/", "*.zip"]
    missing = [x for x in needed if x not in text]
    return [f".gitignore eksik dışlama içeriyor: {', '.join(missing)}"] if missing else []


def check_release_build(project: Path) -> list[str]:
    errors: list[str] = []
    for rel in [
        "scripts/security/build_bys360_secure_release_v1_2.py",
        "scripts/windows/build_bys360_secure_release_v1_2.ps1",
    ]:
        if not (project / rel).exists():
            errors.append(f"Güvenli release üretim dosyası eksik: {rel}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    project = Path(args.project_root).resolve()
    errors: list[str] = []
    errors += check_gitignore(project)
    errors += check_env_example(project)
    errors += check_release_build(project)
    errors += scan_files(project)
    if errors:
        print("BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_2_GATE_FAIL")
        for e in errors:
            print(f" - {e}")
        raise SystemExit(1)
    print("BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_2_GATE_OK")


if __name__ == "__main__":
    main()
