from __future__ import annotations
from pathlib import Path
import sys
REQUIRED = [
    ("app/portal/routes.py", "BYS360_CORPORATE_PORTAL_MEDIA_VIDEO_V2_3_HELPERS"),
    ("app/portal/routes.py", "_save_portal_images(post, request.files.getlist(\"portal_images\"))"),
    ("app/portal/routes.py", "_save_portal_video_link(post, request.form.get(\"video_url\"))"),
    ("app/templates/portal/_composer.html", "BYS360_CORPORATE_PORTAL_MEDIA_VIDEO_V2_3_COMPOSER"),
    ("app/templates/portal/_composer.html", "enctype=\"multipart/form-data\""),
    ("app/templates/portal/_post_card.html", "BYS360_CORPORATE_PORTAL_MEDIA_VIDEO_V2_3_POST_CARD"),
    ("app/static/css/bys360_portal.css", "BYS360_CORPORATE_PORTAL_MEDIA_VIDEO_V2_3_CSS"),
    ("app/static/js/bys360_portal.js", "BYS360_CORPORATE_PORTAL_MEDIA_VIDEO_V2_3_JS"),
]
def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    missing = []
    for rel, marker in REQUIRED:
        path = root / rel
        if not path.exists() or marker not in path.read_text(encoding="utf-8", errors="ignore"):
            missing.append(f"{rel}: {marker}")
    if not (root / "app" / "static" / "uploads" / "portal").exists():
        missing.append("app/static/uploads/portal klasörü yok")
    if missing:
        print("BYS360_CORPORATE_PORTAL_MEDIA_VIDEO_V2_3_GATE_FAIL")
        for item in missing: print(" - " + item)
        return 1
    print("BYS360_CORPORATE_PORTAL_MEDIA_VIDEO_V2_3_GATE_OK")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
