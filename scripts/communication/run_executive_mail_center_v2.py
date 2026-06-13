from __future__ import annotations
import argparse, json
from app import create_app
from app.services.executive_mail_center_v2 import run_due_tasks, run_task

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", default="due")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    app = create_app()
    with app.app_context():
        result = run_due_tasks(dry_run=args.dry_run) if args.task == "due" else run_task(args.task, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result.get("ok", True) else 1)
if __name__ == "__main__": main()
