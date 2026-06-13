# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 Portal V3A basın haber aday taraması")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--manual", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from app import create_app
    from app.services.portal_press_news_service import scan_press_news_candidates
    app = create_app()
    with app.app_context():
        result = scan_press_news_candidates(manual=args.manual)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1

if __name__ == "__main__":
    raise SystemExit(main())
