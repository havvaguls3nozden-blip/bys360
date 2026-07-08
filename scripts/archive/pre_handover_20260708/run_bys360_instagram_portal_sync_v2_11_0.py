from __future__ import annotations

from app import create_app
from app.services.instagram_portal_sync import sync_instagram_to_portal

app = create_app()
with app.app_context():
    result = sync_instagram_to_portal()
    print(result.get("message", result))
    if not result.get("ok", False) and result.get("enabled", False):
        raise SystemExit(2)
