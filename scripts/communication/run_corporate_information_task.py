from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from app import create_app
    from app.services.corporate_information_center import send_task

    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    app = create_app()
    with app.app_context():
        result = send_task(args.task, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") or result.get("skipped") else 1

if __name__ == "__main__":
    raise SystemExit(main())
