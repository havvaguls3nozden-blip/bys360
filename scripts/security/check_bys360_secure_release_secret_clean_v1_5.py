from __future__ import annotations

from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "env", "__pycache__", "dist", "dist_secure", "node_modules", "logs", "uploads", "instance"}
SKIP_SUFFIXES = {".zip", ".7z", ".rar", ".pyc", ".pyo", ".sqlite", ".sqlite3", ".db", ".dump", ".log"}
SECURITY_MAINTENANCE_PREFIXES = (
    "check_bys360_secure_release_secret_clean_",
    "repair_bys360_secure_release_secret_clean_",
    "build_bys360_secure_release_",
)


def should_scan(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    parts = rel.parts
    if any(part in SKIP_DIRS for part in parts):
        return False
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    name = path.name
    rel_posix = rel.as_posix()
    # Güvenlik scriptleri kendi arama imzalarını içerir; kaynakta kalabilir, release dışına alınır.
    if rel_posix.startswith("scripts/security/") and any(name.startswith(prefix) for prefix in SECURITY_MAINTENANCE_PREFIXES):
        return False
    if rel_posix.startswith("scripts/windows/") and name.startswith("build_bys360_secure_release_"):
        return False
    if path.stat().st_size > 2_000_000:
        return False
    return True


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    errors: list[str] = []

    required = [
        root / "scripts/security/build_bys360_secure_release_v1_5.py",
        root / "scripts/windows/build_bys360_secure_release_v1_5.ps1",
        root / "scripts/security/repair_bys360_secure_release_secret_clean_v1_5.py",
        root / "scripts/security/check_bys360_secure_release_secret_clean_v1_5.py",
        root / "docs/deploy/ENV_TEMPLATE.md",
        root / "docs/handover/SCRIPTS_DEVIR_TESLIM_NOTU.md",
    ]
    for p in required:
        if not p.exists():
            errors.append(f"zorunlu dosya eksik: {p.relative_to(root).as_posix()}")

    leaked = "avelox" + "." + "17"
    bad_text = [
        (leaked, "known leaked db password"),
        ('initial_password=<WEAK_PASSWORD_LITERAL_BLOCKED>', "hardcoded initial password"),
        ("initial_password=<WEAK_PASSWORD_LITERAL_BLOCKED>", "hardcoded initial password"),
        ('.set_password(<WEAK_PASSWORD_LITERAL_BLOCKED>)', "hardcoded set_password"),
        (".set_password(<WEAK_PASSWORD_LITERAL_BLOCKED>)", "hardcoded set_password"),
    ]

    for p in root.rglob("*"):
        if not p.is_file() or not should_scan(p, root):
            continue
        rel = p.relative_to(root).as_posix()
        try:
            data = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (scripts/security/check_bys360_secure_release_secret_clean_v1_5.py:68)")
            continue
        for literal, label in bad_text:
            if literal in data:
                errors.append(f"{rel} içinde yasaklı değer bulundu: {label}")

    gitignore = root / ".gitignore"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8", errors="ignore")
        for marker in (".env", "*.dump", "dist_secure/"):
            if marker not in text:
                errors.append(f".gitignore içinde beklenen dışlama yok: {marker}")
    else:
        errors.append(".gitignore bulunamadı")

    env_example = root / ".env.example"
    if env_example.exists():
        errors.append(".env.example kaynakta duruyor; V1.5 release yaklaşımında docs/deploy/ENV_TEMPLATE.md kullanılmalı")

    if errors:
        print("BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_5_GATE_FAIL")
        for e in errors:
            print(f" - {e}")
        return 1

    print("BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_5_GATE_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
