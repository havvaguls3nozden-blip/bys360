from __future__ import annotations

import re
import sys
from pathlib import Path

TEXT_EXTS = {
    ".py", ".ps1", ".html", ".htm", ".jinja", ".jinja2", ".js", ".css",
    ".md", ".txt", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".json",
    ".sql", ".env", ".example"
}

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "dist", "dist_secure", "_upload_parts",
    "uploads", "logs", "instance"
}

# Kendi güvenlik imza dosyaları taranmaz; aksi halde tarayıcı kendi aradığı örneği yakalar.
EXCLUDED_SECURITY_PATTERNS = (
    "check_bys360_secure_release_secret_clean_",
    "repair_bys360_secure_release_secret_clean_",
    "build_bys360_secure_release_",
)

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def should_skip(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = set(rel.parts)
    if parts & EXCLUDED_DIRS:
        return True
    name = path.name
    if name.endswith((".zip", ".pyc", ".pyo", ".log", ".sqlite", ".sqlite3", ".db", ".dump", ".bak", ".backup")):
        return True
    if any(p in name for p in EXCLUDED_SECURITY_PATTERNS):
        return True
    return False

def iter_text_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if should_skip(p, root):
            continue
        if p.suffix.lower() in TEXT_EXTS or p.name in {".gitignore", ".env", ".env.example"}:
            yield p

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    gitignore = root / ".gitignore"
    gi = read_text(gitignore) if gitignore.exists() else ""
    for token in [".env", ".env.*", "*.log", "*.zip", "dist_secure/"]:
        if token not in gi:
            errors.append(f".gitignore güvenli dışlama eksik: {token}")

    if not (root / "docs" / "deploy" / "ENV_TEMPLATE.md").exists():
        errors.append("docs/deploy/ENV_TEMPLATE.md yok")

    if not (root / "app" / "security" / "passwords.py").exists():
        errors.append("app/security/passwords.py yok")
    else:
        pwd = read_text(root / "app" / "security" / "passwords.py")
        if "generate_initial_password" not in pwd or "secrets" not in pwd:
            errors.append("generate_initial_password güvenli helper eksik")

    leaked = "avelox" + "." + "17"
    sentry_placeholder = "https://" + "..." + "@sentry.io" + "/..."
    hardcoded_patterns = [
        ('initial_password=<WEAK_PASSWORD_LITERAL_BLOCKED>', "hardcode initial_password"),
        ("initial_password=<WEAK_PASSWORD_LITERAL_BLOCKED>", "hardcode initial_password"),
        ('.set_password(<WEAK_PASSWORD_LITERAL_BLOCKED>)', "hardcode set_password"),
        (".set_password(<WEAK_PASSWORD_LITERAL_BLOCKED>)", "hardcode set_password"),
        (leaked, "known leaked db password"),
    ]

    for p in iter_text_files(root):
        text = read_text(p)
        rel = p.relative_to(root).as_posix()

        # Yerel .env, gerçek release paketine alınmayacak. Bu gate sadece bilinen gerçek sızıntıları
        # ve kod içi sabit şifreleri yakalar; Sentry placeholder yerelde fail sebebi değildir.
        for literal, label in hardcoded_patterns:
            if literal in text:
                errors.append(f"{rel} içinde yasaklı değer bulundu: {label}")

        if p.name != ".env" and sentry_placeholder in text:
            # Doküman/runbook örnekleri bile devirde kafa karıştırmasın.
            warnings.append(f"{rel} içinde Sentry placeholder örneği var; release build bunu dışlar veya temizler.")

    if errors:
        print("BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_4_GATE_FAIL")
        for e in errors:
            print(f" - {e}")
        for w in warnings:
            print(f" - UYARI: {w}")
        return 1

    print("BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_4_GATE_OK")
    for w in warnings:
        print(f" - UYARI: {w}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
