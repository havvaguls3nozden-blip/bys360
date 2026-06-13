# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MENU_KEY = "performance_personnel_category_card"
MENU_URL = "/performance/v2-1-3-personnel-category-card"
RULE_VERSION = "performance_v2_1_3a_personnel_category_sidebar"
SUCCESS_MARKER = "BYS360_PERFORMANCE_V2_1_3A_PERSONNEL_CATEGORY_SIDEBAR_CHECK_OK"
FAIL_MARKER = "BYS360_PERFORMANCE_V2_1_3A_PERSONNEL_CATEGORY_SIDEBAR_CHECK_FAIL"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    sys.path.insert(0, str(root))

    result = {"project_root": str(root), "rule_version": RULE_VERSION, "checks": []}
    try:
        from app import create_app
        app = create_app()
        with app.app_context():
            from app.live_scope import is_live_settings_menu_key
            from app.menu_registry import flatten_menu_definitions, ROLE_MENU_DEFAULTS
            from app.models import RoleMenuDefault
            from flask import url_for

            live_ok = bool(is_live_settings_menu_key(MENU_KEY))
            result["checks"].append({"name": "live_scope", "ok": live_ok})

            item = next((row for row in flatten_menu_definitions() if row.get("key") == MENU_KEY), None)
            result["checks"].append({"name": "menu_item", "ok": bool(item), "item": item or {}})

            with app.test_request_context():
                url = url_for("main.performance_v2_1_3_personnel_category_card")
            result["checks"].append({"name": "endpoint", "ok": url == MENU_URL, "url": url})

            role_ok = MENU_KEY in set(ROLE_MENU_DEFAULTS.get("admin", set()))
            result["checks"].append({"name": "admin_role_default", "ok": role_ok})

            db_count = RoleMenuDefault.query.filter_by(menu_key=MENU_KEY, is_visible=True).count()
            result["checks"].append({"name": "db_role_defaults", "ok": db_count >= 1, "count": db_count})

        result["ok"] = all(c.get("ok") for c in result["checks"])
    except Exception as exc:
        result["ok"] = False
        result["error"] = str(exc)

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    print(SUCCESS_MARKER if result.get("ok") else FAIL_MARKER)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
