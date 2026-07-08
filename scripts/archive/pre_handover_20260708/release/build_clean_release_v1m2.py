from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\bys360\project").resolve()
RELEASE_DIR = Path(r"C:\bys360\releases").resolve()

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".dart_tool",
    ".gradle",
    "backups",
    "archive",
    "overlays",
    "instance",
    "local_storage",
    "node_modules",
    "build",
    "dist",
    "dist_secure",
    "logs",
    "reports",
}

EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".log",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".bak",
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
    ".dill",
    ".stamp",
    ".lock",
    ".bin",
}

EXCLUDED_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "local.properties",
    "key.properties",
    "flutter_export_environment.sh",
    "flutter_native_integration.env",
    "secret_hygiene_report.json",
}

SECRET_LIKE_SUFFIXES = {
    ".key",
    ".pem",
    ".p12",
    ".pfx",
    ".ppk",
    ".jks",
    ".keystore",
}

ALLOWED_NAMES = {
    ".env.example",
    "key.properties.example",
}

def is_excluded(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = set(rel.parts)
    name = path.name
    lower_name = name.lower()

    if parts & EXCLUDED_DIRS:
        return True

    if name in ALLOWED_NAMES:
        return False

    if lower_name in EXCLUDED_NAMES:
        return True

    if lower_name.startswith(".env") and lower_name != ".env.example":
        return True

    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True

    if path.suffix.lower() in SECRET_LIKE_SUFFIXES:
        return True

    if ".bak_" in lower_name or lower_name.endswith(".bak"):
        return True

    return False

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def assert_clean(included_rel: list[str]) -> list[str]:
    bad_patterns = [
        r"(^|/)\.env($|\.local$|\.production$|\.development$|\.prod$|\.dev$|\.test$)",
        r"(^|/)backups/",
        r"(^|/)overlays/",
        r"(^|/)archive/",
        r"(^|/)logs/",
        r"(^|/)reports/",
        r"(^|/)dist_secure/",
        r"(^|/)__pycache__/",
        r"(^|/)\.dart_tool/",
        r"(^|/)\.gradle/",
        r"(^|/)node_modules/",
        r"(^|/)local_storage/",
        r"(^|/)instance/",
        r"\.pyc$",
        r"\.sqlite3?$",
        r"\.db$",
        r"\.log(\.|$)",
        r"\.zip$",
        r"\.dill$",
        r"key\.properties$",
        r"local\.properties$",
        r"flutter_export_environment\.sh$",
        r"flutter_native_integration\.env$",
        r"\.(pem|p12|pfx|ppk|jks|keystore|key)$",
    ]

    compiled = [re.compile(p, re.IGNORECASE) for p in bad_patterns]
    return [p for p in included_rel if any(rx.search(p) for rx in compiled)]

def main() -> int:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = RELEASE_DIR / f"BYS360_CLEAN_RELEASE_V1M2_{stamp}.zip"
    manifest_path = RELEASE_DIR / f"BYS360_CLEAN_RELEASE_V1M2_{stamp}.manifest.json"
    sha_path = RELEASE_DIR / f"BYS360_CLEAN_RELEASE_V1M2_{stamp}.sha256.txt"

    included: list[Path] = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if is_excluded(path):
            continue
        included.append(path)

    included_rel = [p.relative_to(ROOT).as_posix() for p in included]
    blocked = assert_clean(included_rel)

    if blocked:
        print("HATA: Release paketi hâlâ temiz değil. Engellenen dosyalar:")
        print(json.dumps(blocked[:200], ensure_ascii=False, indent=2))
        print(f"TOPLAM ENGELLENEN: {len(blocked)}")
        return 2

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in included:
            zf.write(path, path.relative_to(ROOT).as_posix())

    zip_sha = sha256_file(zip_path)

    manifest = {
        "release": "BYS360 Clean Release V1M2",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(ROOT),
        "zip": str(zip_path),
        "included_count": len(included_rel),
        "zip_sha256": zip_sha,
        "excluded_dirs": sorted(EXCLUDED_DIRS),
        "excluded_suffixes": sorted(EXCLUDED_SUFFIXES),
        "excluded_names": sorted(EXCLUDED_NAMES),
        "included_files": included_rel,
    }

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    sha_path.write_text(f"{zip_sha}  {zip_path.name}\n", encoding="utf-8")

    print("OK: Temiz release paketi üretildi.")
    print(f"ZIP: {zip_path}")
    print(f"MANIFEST: {manifest_path}")
    print(f"SHA256: {sha_path}")
    print(f"INCLUDED: {len(included_rel)}")
    print(f"SHA256 HASH: {zip_sha}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())

