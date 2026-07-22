from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.file_center.maintenance_service import run_file_center_maintenance_tick


def main() -> int:
    app = create_app()
    with app.app_context():
        result = run_file_center_maintenance_tick(actor_user_id=None, scan_limit=250)
        db.session.commit()
        print("OK: Dosya Merkezi canlı bakım döngüsü tamamlandı.")
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
