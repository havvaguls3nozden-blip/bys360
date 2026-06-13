from __future__ import annotations

import argparse
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TARGET_REL = "app/templates/performance/archive/index.html"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_P14J_PERFORMANCE_ARCHIVE_TEMPLATE_RESTORE_CHECK_START")
    print(f"project_root={project_root}")

    if not target.exists():
        raise SystemExit(f"TEMPLATE_NOT_FOUND: {target}")

    env = Environment(loader=FileSystemLoader(str(project_root / "app" / "templates")))
    env.get_template("performance/archive/index.html")

    text = target.read_text(encoding="utf-8", errors="ignore")
    result = {
        "template_exists": True,
        "syntax_ok": True,
        "extends_base": 'extends "base.html"' in text or "extends 'base.html'" in text,
        "has_content_block": "block content" in text,
        "line_count": len(text.splitlines()),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("BYS360_P14J_PERFORMANCE_ARCHIVE_TEMPLATE_RESTORE_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
