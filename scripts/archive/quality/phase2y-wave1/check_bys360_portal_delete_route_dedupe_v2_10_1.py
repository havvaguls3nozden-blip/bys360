# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", "--project-root", dest="project_root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    routes = root / "app" / "portal" / "routes.py"
    text = routes.read_text(encoding="utf-8")
    block_count = len(re.findall(r"(?ms)^(?:@[^\n]+\n)+def\s+portal_post_delete\s*\(", text))
    errors = []
    if block_count != 1:
        errors.append(f"portal_post_delete blok sayısı: {block_count}")
    if text.count('/portal/posts/<int:post_id>/delete') != 1:
        errors.append("delete route string tekil değil")
    if errors:
        print("BYS360_PORTAL_DELETE_ROUTE_DEDUPE_V2_10_1_QUALITY_FAIL")
        for e in errors:
            print(" - " + e)
        return 1
    print("BYS360_PORTAL_DELETE_ROUTE_DEDUPE_V2_10_1_QUALITY_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
