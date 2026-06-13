from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\bys360\project")
sys.path.insert(0, str(ROOT))


def main() -> int:
    from app import create_app
    from app.services.cic.facade import run_due_tasks

    app = create_app()
    with app.app_context():
        result = run_due_tasks()
        print("=" * 80)
        print("RUN_AT=", datetime.now().isoformat(timespec="seconds"))
        print(json.dumps(result, ensure_ascii=False, default=str, indent=2))
        if result.get("weekend_blocked"):
            print("BYS360_CIC_WEEKEND_MAIL_BLOCKED_OK")
        return 0 if result.get("ok") else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print("UNHANDLED_EXCEPTION")
        traceback.print_exc()
        raise SystemExit(1)
