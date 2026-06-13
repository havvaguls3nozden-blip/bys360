from __future__ import annotations

import datetime as dt
import zipfile
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "dist", "dist_secure", "_upload_parts",
    "uploads", "logs", "instance"
}

EXCLUDED_SUFFIXES = {
    ".pyc", ".pyo", ".log", ".sqlite", ".sqlite3", ".db", ".dump",
    ".bak", ".backup", ".zip", ".7z", ".rar"
}

EXCLUDED_NAMES = {
    ".env", ".env.example", ".DS_Store"
}

OLD_SECURITY_SCRIPT_PREFIXES = (
    "check_bys360_secure_release_secret_clean_v1",
    "repair_bys360_secure_release_secret_clean_v1",
    "build_bys360_secure_release_v1",
)

KEEP_V14 = (
    "check_bys360_secure_release_secret_clean_v1_4",
    "repair_bys360_secure_release_secret_clean_v1_4",
    "build_bys360_secure_release_v1_4",
)

def should_exclude(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = rel.parts
    if any(part in EXCLUDED_DIRS for part in parts):
        return True

    name = path.name
    if name in EXCLUDED_NAMES:
        return True
    if name.startswith(".env"):
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True

    rel_posix = rel.as_posix()
    if rel_posix.startswith("scripts/security/") or rel_posix.startswith("scripts/windows/build_bys360_secure_release_v1"):
        if any(k in name for k in KEEP_V14):
            return False
        if any(name.startswith(prefix) for prefix in OLD_SECURITY_SCRIPT_PREFIXES):
            return True

    return False

def validate_zip(zip_path: Path) -> list[str]:
    errors: list[str] = []
    leaked = "avelox" + "." + "17"
    sentry_placeholder = "https://" + "..." + "@sentry.io" + "/..."
    bad_text = [
        (leaked, "known leaked db password"),
        ('initial_password=<WEAK_PASSWORD_LITERAL_BLOCKED>', "hardcoded initial password"),
        ("initial_password=<WEAK_PASSWORD_LITERAL_BLOCKED>", "hardcoded initial password"),
        ('.set_password(<WEAK_PASSWORD_LITERAL_BLOCKED>)', "hardcoded set_password"),
        (".set_password(<WEAK_PASSWORD_LITERAL_BLOCKED>)", "hardcoded set_password"),
        (sentry_placeholder, "sentry placeholder url"),
    ]

    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            name = info.filename
            base = Path(name).name
            if base.startswith(".env"):
                errors.append(f"release içinde env dosyası var: {name}")
                continue
            if info.file_size > 2_000_000:
                continue
            try:
                data = zf.read(info).decode("utf-8", errors="ignore")
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (scripts/security/build_bys360_secure_release_v1_4.py:81)")
                continue
            for literal, label in bad_text:
                if literal in data:
                    errors.append(f"release içinde yasaklı değer bulundu ({label}): {name}")
    return errors

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    out_dir = root / "dist_secure"
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = out_dir / f"BYS360_SECURE_RELEASE_V1_4_{stamp}.zip"

    included = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if should_exclude(p, root):
                continue
            rel = p.relative_to(root).as_posix()
            zf.write(p, rel)
            included += 1

    errors = validate_zip(zip_path)
    if errors:
        try:
            zip_path.unlink()
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (scripts/security/build_bys360_secure_release_v1_4.py)")
        print("BYS360_SECURE_RELEASE_BUILD_V1_4_FAIL")
        for e in errors:
            print(f" - {e}")
        return 1

    print("BYS360_SECURE_RELEASE_BUILD_V1_4_OK")
    print(f" - zip: {zip_path}")
    print(f" - files: {included}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
