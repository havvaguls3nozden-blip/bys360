from __future__ import annotations

import argparse
import inspect
import json
import sys
from datetime import datetime
from pathlib import Path

# Proje kökünü Python import yoluna ekle
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.services.mail_performance_sender import run_performance_mail_automation


def _json_default(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="BYS360 performans mail hatırlatma otomasyon runner"
    )
    parser.add_argument("--hour", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        sig = inspect.signature(run_performance_mail_automation)
        kwargs = {}

        if "dry_run" in sig.parameters:
            kwargs["dry_run"] = args.dry_run

        if "hour" in sig.parameters and args.hour is not None:
            kwargs["hour"] = args.hour

        if "run_hour" in sig.parameters and args.hour is not None:
            kwargs["run_hour"] = args.hour

        if "force" in sig.parameters:
            kwargs["force"] = args.force

        result = run_performance_mail_automation(**kwargs)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=_json_default))

        if isinstance(result, dict) and result.get("failed_count", 0):
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
