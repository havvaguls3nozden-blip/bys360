from __future__ import annotations

import argparse, json
from app import create_app
from app.services.corporate_information_center_engine import run_task

ALIASES = {
    "staff_morning": "PERSONEL_MORNING",
    "staff_noon": "PERSONEL_NOON",
    "staff_evening": "PERSONEL_EVENING",
    "manager_morning": "MANAGER_MORNING",
    "manager_evening": "MANAGER_EVENING",
}

def main() -> int:
    p = argparse.ArgumentParser(description="BYS360 Kurumsal Bilgilendirme Merkezi görev çalıştırıcı")
    p.add_argument("--task", "--task-key", dest="task", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    key = ALIASES.get(args.task, args.task)
    app = create_app()
    with app.app_context():
        result = run_task(key, dry_run=args.dry_run, force=args.force)
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0 if result.get("ok") else 2

if __name__ == "__main__":
    raise SystemExit(main())
