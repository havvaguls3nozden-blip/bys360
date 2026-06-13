from __future__ import annotations
from pathlib import Path
import sys

REQUIRED_MARKERS = [
    ("app/portal/routes.py", "PORTAL_MAX_MEDIA_BYTES = 50 * 1024 * 1024"),
    ("app/portal/routes.py", "_save_portal_video_file(post, request.files.getlist(\"portal_video_file\"))"),
    ("app/portal/routes.py", "def portal_mention_users"),
    ("app/portal/routes.py", "_save_comment_mentions"),
    ("app/portal/routes.py", "_notify_comment_reply"),
    ("app/models/portal_models.py", "parent_comment_id"),
    ("app/models/portal_models.py", "class PortalCommentMention"),
    ("app/models/__init__.py", "PortalCommentMention"),
    ("app/services/portal_service.py", "BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_SERVICE"),
    ("app/templates/portal/_composer.html", "name=\"portal_video_file\""),
    ("app/templates/portal/_composer.html", "50 MB"),
    ("app/templates/portal/_post_card.html", "portal-native-video-frame"),
    ("app/templates/portal/_post_card.html", "data-portal-reply-toggle"),
    ("app/templates/portal/_post_card.html", "data-portal-mention"),
    ("app/static/js/bys360_portal.js", "BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_JS"),
    ("app/static/css/bys360_portal.css", "BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_CSS"),
    ("migrations/versions/bys360_portal_media_comments_mentions_v2_12_1.py", "portal_comment_mentions"),
]


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    missing: list[str] = []
    for rel, marker in REQUIRED_MARKERS:
        path = root / rel
        if not path.exists():
            missing.append(f"{rel}: dosya yok")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if marker not in text:
            missing.append(f"{rel}: marker yok -> {marker}")

    composer = (root / "app/templates/portal/_composer.html").read_text(encoding="utf-8", errors="ignore") if (root / "app/templates/portal/_composer.html").exists() else ""
    if "8 MB sınırı" in composer:
        missing.append("app/templates/portal/_composer.html: eski 8 MB metni kaldı")

    if missing:
        print("BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_GATE_FAIL")
        for item in missing:
            print(" - " + item)
        return 1

    print("BYS360_PORTAL_MEDIA_COMMENTS_MENTIONS_V2_12_1_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
