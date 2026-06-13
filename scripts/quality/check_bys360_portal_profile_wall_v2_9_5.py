# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    routes = root / "app" / "portal" / "routes.py"
    text = routes.read_text(encoding="utf-8")
    failures = []
    if '@bp.route("/portal/posts/<int:post_id>/delete"' in text or "@bp.route('/portal/posts/<int:post_id>/delete'" in text:
        failures.append("@bp.route silme route'unda kalmış")
    if "def portal_delete_post" not in text:
        failures.append("portal_delete_post yok")
    if "/portal/posts/<int:post_id>/delete" not in text:
        failures.append("delete route path yok")
    if failures:
        print("BYS360_PORTAL_PROFILE_WALL_V2_9_5_QUALITY_FAIL")
        for f in failures:
            print(f" - {f}")
        return 1
    print("BYS360_PORTAL_PROFILE_WALL_V2_9_5_QUALITY_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
