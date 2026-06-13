import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:\bys360\project")
sys.path.insert(0, str(ROOT))

TASK_KEY = "staff_noon"

def _as_dict(result):
    if isinstance(result, dict):
        return result
    if hasattr(result, "__dict__"):
        return dict(result.__dict__)
    return {"result": str(result)}

try:
    from app import create_app
    from app.services.cic.facade import send_task

    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("RUN_AT=", datetime.now().isoformat(timespec="seconds"))
        print("TASK_KEY=", TASK_KEY)

        result = send_task(TASK_KEY)
        data = _as_dict(result)

        print("RESULT=", json.dumps(data, ensure_ascii=False, default=str))

        failed = (
            data.get("failed")
            or data.get("failed_count")
            or data.get("error_count")
            or 0
        )
        success = (
            data.get("success")
            or data.get("success_count")
            or data.get("sent_count")
            or 0
        )

        print(f"SUMMARY= success:{success} failed:{failed}")

        if int(failed or 0) > 0:
            sys.exit(2)

        sys.exit(0)

except Exception:
    print("UNHANDLED_EXCEPTION")
    traceback.print_exc()
    sys.exit(1)
