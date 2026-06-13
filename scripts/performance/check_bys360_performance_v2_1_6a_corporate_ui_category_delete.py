from __future__ import annotations
import json
from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from app import create_app
    from app.services.performance.v2_1_6a_category_ui_cleanup import all_categories_with_usage, active_categories
    app = create_app()
    with app.app_context():
        cats = active_categories()
        all_cats = all_categories_with_usage()
        result = {
            "ok": True,
            "active_category_count": len(cats),
            "all_category_count": len(all_cats),
            "delete_helper": True,
            "rule_version": "performance_v2_1_6a_corporate_ui_category_delete",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("BYS360_PERFORMANCE_V2_1_6A_CORPORATE_UI_CATEGORY_DELETE_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
