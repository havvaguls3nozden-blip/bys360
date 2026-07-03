from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.file_center.services import scan_pending_files, security_summary

app = create_app()
with app.app_context():
    result = scan_pending_files(limit=500, actor_user_id=None)
    db.session.commit()
    summary = security_summary()
    print("OK: V1H güvenlik tarama kuyruğu çalıştırıldı.")
    print(f"Taranan: {result['total']}")
    print(f"Güvenli: {result['clean']}")
    print(f"Karantina: {result['quarantined']}")
    print(f"Engelli: {result['blocked']}")
    print(f"Başarısız: {result['failed']}")
    print("Güncel özet:")
    print(summary)
