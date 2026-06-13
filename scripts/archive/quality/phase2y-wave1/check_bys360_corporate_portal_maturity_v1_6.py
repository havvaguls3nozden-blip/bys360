# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
checks = [
    ("app/templates/portal/_composer.html", "data-portal-visibility-help"),
    ("app/templates/portal/_post_card.html", "portal-comment-closed"),
    ("app/templates/portal/groups.html", "portal-create-group-card"),
    ("app/templates/portal/_home_feed.html", "portal-home-action"),
    ("app/static/css/bys360_portal.css", "@media(max-width:720px)"),
    ("app/static/js/bys360_portal.js", "Yayınlanıyor"),
]
errors = []
for rel, token in checks:
    path = ROOT / rel
    if not path.exists() or token not in path.read_text(encoding="utf-8"):
        errors.append(f"{rel} içinde beklenen kontrol bulunamadı: {token}")
if errors:
    for err in errors:
        print(" - " + err)
    raise SystemExit("BYS360_CORPORATE_PORTAL_MATURITY_V1_6_QUALITY_FAIL")
print("BYS360_CORPORATE_PORTAL_MATURITY_V1_6_QUALITY_OK")
