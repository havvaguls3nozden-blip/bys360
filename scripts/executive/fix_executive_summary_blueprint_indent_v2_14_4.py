# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

IMPORT_LINE = "from app.executive_summary import executive_summary_bp"
REGISTER_EXPR = "app.register_blueprint(executive_summary_bp)"


def detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def patch_init(init_path: Path) -> None:
    if not init_path.exists():
        raise FileNotFoundError(f"Bulunamadı: {init_path}")

    raw = init_path.read_text(encoding="utf-8", errors="ignore")
    nl = detect_newline(raw)

    backup = init_path.with_suffix(init_path.suffix + f".bak_v2_14_4_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(init_path, backup)

    lines = raw.splitlines()

    # Önce önceki hatalı/tekrarlı eklemeleri temizle.
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == IMPORT_LINE:
            continue
        if stripped == REGISTER_EXPR:
            continue
        cleaned.append(line)
    lines = cleaned

    # Import satırını son import bloğundan sonra ekle.
    if not any(line.strip() == IMPORT_LINE for line in lines):
        insert_at = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_at = i + 1
        lines.insert(insert_at, IMPORT_LINE)

    # create_app içindeki return app öncesine doğru girintiyle register ekle.
    return_indexes = [i for i, line in enumerate(lines) if re.match(r"^\s*return\s+app\s*$", line)]
    if not return_indexes:
        raise RuntimeError("app/__init__.py içinde 'return app' bulunamadı; blueprint kaydı otomatik yapılamadı.")

    # Genellikle create_app içindeki son return app doğru noktadır.
    idx = return_indexes[-1]
    indent = re.match(r"^(\s*)", lines[idx]).group(1)
    register_line = f"{indent}{REGISTER_EXPR}"

    if not any(line.strip() == REGISTER_EXPR for line in lines):
        lines.insert(idx, register_line)

    new_text = nl.join(lines) + nl
    init_path.write_text(new_text, encoding="utf-8")
    print(f"OK: app/__init__.py blueprint girintisi düzeltildi.")
    print(f"Yedek: {backup}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root)
    patch_init(root / "app" / "__init__.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
