from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', required=True)
    parser.add_argument('--manual', action='store_true')
    parser.add_argument('--auto-discover', action='store_true')
    parser.add_argument('--url', action='append', default=[])
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    sys.path.insert(0, str(root))
    from app import create_app
    from app.services.portal_social_embed_service import queue_social_urls, run_social_embed_scan
    app = create_app()
    with app.app_context():
        if args.url:
            queue_social_urls(args.url)
        result = run_social_embed_scan(manual=args.manual, auto_discover=args.auto_discover)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0 if result.get('ok') else 1

if __name__ == '__main__':
    raise SystemExit(main())
