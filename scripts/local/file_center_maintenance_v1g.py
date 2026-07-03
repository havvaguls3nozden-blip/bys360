from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.file_center.maintenance_service import expire_due_links_and_requests, recalculate_quotas

app = create_app()
with app.app_context():
    expired = expire_due_links_and_requests(actor_user_id=None)
    quota = recalculate_quotas(actor_user_id=None)
    db.session.commit()
    print("OK: Dosya Merkezi V1G bakım scripti tamamlandı.")
    print(f"Süresi dolan link: {expired['links']}")
    print(f"Süresi dolan dosya isteği: {expired['requests']}")
    print(f"Kota güncellenen kullanıcı: {quota['users']}")
    print(f"Aktif dosya: {quota['files']}")
