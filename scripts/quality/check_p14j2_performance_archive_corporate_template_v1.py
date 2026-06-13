from __future__ import annotations

import argparse
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TARGET_REL = "app/templates/performance/archive/index.html"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_P14J2_PERFORMANCE_ARCHIVE_CORPORATE_RESTORE_CHECK_START")
    print(f"project_root={project_root}")

    if not target.exists():
        raise SystemExit(f"TEMPLATE_NOT_FOUND: {target}")

    env = Environment(loader=FileSystemLoader(str(project_root / "app" / "templates")))
    env.get_template("performance/archive/index.html")

    text = read_text(target)
    result = {
        "template_exists": True,
        "syntax_ok": True,
        "extends_base": 'extends "base.html"' in text or "extends 'base.html'" in text,
        "has_elite_css_link": "bys360_performance_surfaces_elite_v2.css" in text,
        "has_archive_marker": "BYS360_PERFORMANCE_ARCHIVE_CORPORATE_RESTORE_P14J2" in text,
        "has_generic_p14j_empty_icon": "📁" in text,
        "line_count": len(text.splitlines()),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["has_archive_marker"]:
        raise SystemExit("P14J2_CHECK_FAIL archive marker not found")
    if result["has_generic_p14j_empty_icon"]:
        raise SystemExit("P14J2_CHECK_FAIL old generic fallback marker still present")

    print("BYS360_P14J2_PERFORMANCE_ARCHIVE_CORPORATE_RESTORE_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
