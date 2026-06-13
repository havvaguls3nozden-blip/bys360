from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from app import create_app
from app.services.corporate_information_center_engine import run_task


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 Kurumsal Bilgilendirme Merkezi görev çalıştırıcı")
    parser.add_argument("--task-key", required=True, choices=["PERSONEL_MORNING", "PERSONEL_NOON", "PERSONEL_EVENING", "MANAGER_MORNING", "MANAGER_EVENING"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--log-file", default="")
    args = parser.parse_args()
    app = create_app()
    with app.app_context():
        result = run_task(args.task_key, dry_run=args.dry_run, force=args.force)
    line = json.dumps(result, ensure_ascii=False, default=str)
    print(line)
    if args.log_file:
        p = Path(args.log_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {line}\n")
    return 0 if result.get("ok") else 2

if __name__ == "__main__":
    raise SystemExit(main())
