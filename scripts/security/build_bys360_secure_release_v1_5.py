from __future__ import annotations

import datetime as dt
import zipfile
from pathlib import Path, PurePosixPath

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "dist", "dist_secure", "_upload_parts", "uploads", "logs", "instance",
    "backups", "backup", "archive", "payload", "overlay_payload", "_security_quarantine",
    "_local_quarantine", "_cleanup_quarantine", "_local_secrets"
}

EXCLUDED_SUFFIXES = {
    ".pyc", ".pyo", ".log", ".sqlite", ".sqlite3", ".db", ".dump", ".bak", ".backup", ".zip", ".7z", ".rar"
}

EXCLUDED_NAMES = {
    ".env", ".env.example", ".DS_Store"
}

# Release paketine bakım/gate scriptlerini koymuyoruz. Bu scriptler kaynak projede kalır,
# fakat devir/release zip'i sade ve uygulanabilir kaynak kod + doküman içerir.
SECURITY_MAINTENANCE_PREFIXES = (
    "check_bys360_secure_release_secret_clean_",
    "repair_bys360_secure_release_secret_clean_",
    "build_bys360_secure_release_",
)
WINDOWS_RELEASE_BUILD_PREFIX = "build_bys360_secure_release_"

DOCS_TO_EXCLUDE = {
    "docs/security/P0_SENTRY_DBSSL_CSP_V2_RUNBOOK.md",
}


def should_exclude(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = rel.parts
    rel_posix = rel.as_posix()

    if any(part in EXCLUDED_DIRS for part in parts):
        return True

    name = path.name
    if name in EXCLUDED_NAMES:
        return True
    if name.startswith(".env"):
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True

    if rel_posix in DOCS_TO_EXCLUDE:
        return True

    if rel_posix.startswith("scripts/security/") and any(name.startswith(prefix) for prefix in SECURITY_MAINTENANCE_PREFIXES):
        return True

    if rel_posix.startswith("scripts/windows/") and name.startswith(WINDOWS_RELEASE_BUILD_PREFIX):
        return True

    # Eski overlay klasörleri veya geçici inspect/work klasörleri release'e girmesin.
    lower_rel = rel_posix.lower()
    if any(marker in lower_rel for marker in ("overlay", "inspect", "_work", "work_bys")) and not lower_rel.startswith(("app/", "docs/", "scripts/")):
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
            parts = set(PurePosixPath(name).parts) if "PurePosixPath" in globals() else set(Path(name).parts)
            blocked_dirs = {
                ".git", ".venv", "venv", "env", "backups", "backup", "archive", "payload", "overlay_payload",
                "logs", "instance", "uploads", "_upload_parts", "_security_quarantine", "_local_quarantine",
                "_cleanup_quarantine", "_local_secrets"
            }
            bad_parts = sorted(parts & blocked_dirs)
            if bad_parts:
                errors.append(f"release içinde yasaklı klasör var ({bad_parts[0]}): {name}")
                continue
            if base.startswith(".env"):
                errors.append(f"release içinde env dosyası var: {name}")
                continue
            if name.startswith("scripts/security/") and any(base.startswith(prefix) for prefix in SECURITY_MAINTENANCE_PREFIXES):
                errors.append(f"release içinde bakım/gate scripti var: {name}")
                continue
            if name.startswith("scripts/windows/") and base.startswith(WINDOWS_RELEASE_BUILD_PREFIX):
                errors.append(f"release içinde release build wrapper scripti var: {name}")
                continue
            if info.file_size > 2_000_000:
                continue
            try:
                data = zf.read(info).decode("utf-8", errors="ignore")
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (scripts/security/build_bys360_secure_release_v1_5.py:97)")
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
    if not root.exists():
        print("BYS360_SECURE_RELEASE_BUILD_V1_5_FAIL")
        print(f" - ProjectRoot bulunamadı: {root}")
        return 1

    out_dir = root / "dist_secure"
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = out_dir / f"BYS360_SECURE_RELEASE_V1_5_{stamp}.zip"

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
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (scripts/security/build_bys360_secure_release_v1_5.py)")
        print("BYS360_SECURE_RELEASE_BUILD_V1_5_FAIL")
        for e in errors:
            print(f" - {e}")
        return 1

    print("BYS360_SECURE_RELEASE_BUILD_V1_5_OK")
    print(f" - zip: {zip_path}")
    print(f" - files: {included}")
    print(" - not: .env/.env.example, .venv, .git, backups/archive ve güvenlik bakım scriptleri release dışı bırakıldı")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
