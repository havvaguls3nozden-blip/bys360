from __future__ import annotations

import argparse
import datetime as dt
import zipfile
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules", "dist", "dist_secure", "_upload_parts", "uploads", "logs", "log", "instance"
}
EXCLUDED_EXTS = {".pyc", ".pyo", ".zip", ".7z", ".rar", ".log", ".db", ".sqlite", ".sqlite3", ".dump"}
EXCLUDED_NAMES = {".env", ".flaskenv"}


def is_excluded(path: Path, project: Path) -> bool:
    rel = path.relative_to(project)
    if set(rel.parts) & EXCLUDED_DIRS:
        return True
    if path.name in EXCLUDED_NAMES:
        return True
    if path.name.startswith(".env."):
        return True
    if path.suffix.lower() in EXCLUDED_EXTS:
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    project = Path(args.project_root).resolve()
    dist = project / "dist_secure"
    dist.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = dist / f"BYS360_SECURE_RELEASE_V1_1_{stamp}.zip"
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as zf:
        for path in project.rglob("*"):
            if not path.is_file() or is_excluded(path, project):
                continue
            rel = path.relative_to(project)
            zf.write(path, rel.as_posix())
    print("BYS360_SECURE_RELEASE_V1_1_BUILD_OK")
    print(str(out))


if __name__ == "__main__":
    main()
