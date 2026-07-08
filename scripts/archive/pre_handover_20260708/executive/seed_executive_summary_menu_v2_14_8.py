from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from app import create_app, db
except Exception as exc:
    print(f"WARN: Flask app import edilemedi, sadece template menu uygulanmis olabilir: {exc}")
    raise SystemExit(0)

app = create_app()
with app.app_context():
    print("OK: Flask app acildi. Menu DB seed bu projede model adlari degisebildigi icin guvenli modda atlandi.")
