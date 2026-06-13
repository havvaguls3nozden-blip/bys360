# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

IMPORT_LINE = "from app.executive_summary import executive_summary_bp"
REGISTER_LINE = "    app.register_blueprint(executive_summary_bp)"


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "executive_summary_bp" in text:
        print(f"Blueprint kaydı zaten var: {path}")
        return True

    if "def create_app" not in text:
        print(f"create_app bulunamadı, atlandı: {path}")
        return False

    if IMPORT_LINE not in text:
        lines = text.splitlines()
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert_at = i + 1
        lines.insert(insert_at, IMPORT_LINE)
        text = "\n".join(lines) + "\n"

    marker = "return app"
    if marker in text:
        text = text.replace(marker, REGISTER_LINE + "\n    " + marker, 1)
        path.write_text(text, encoding="utf-8")
        print(f"Blueprint kaydı eklendi: {path}")
        return True

    print(f"return app bulunamadı, manuel kayıt gerekebilir: {path}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root)
    candidates = [root / "app" / "__init__.py", root / "app.py", root / "wsgi.py"]
    for path in candidates:
        if path.exists() and patch_file(path):
            return 0
    print("UYARI: Blueprint otomatik kaydedilemedi. app/__init__.py içinde executive_summary_bp manuel kaydedilmelidir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
