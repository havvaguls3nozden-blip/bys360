from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 günlük personel hava durumu bilgilendirme maili gönderir.")
    parser.add_argument("--force", action="store_true", help="Pasif/günlük tekrar korumasını bypass ederek çalıştırır.")
    parser.add_argument("--dry-run", action="store_true", help="Mail göndermeden kayıt/log test çalışması yapar.")
    args = parser.parse_args()

    root = _project_root()
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from app import create_app
    from app.services.daily_weather_mail import run_daily_weather_mail

    app = create_app()
    with app.app_context():
        result = run_daily_weather_mail(actor_user_id=None, force=bool(args.force), dry_run=bool(args.dry_run))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") or result.get("skipped") else 2


if __name__ == "__main__":
    raise SystemExit(main())
