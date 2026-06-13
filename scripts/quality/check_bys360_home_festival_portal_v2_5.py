from __future__ import annotations

import sys
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def main() -> int:
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    required = {
        "app/templates/home.html": ["bys360_home_festival_portal_v2_5.css", "bys360_home_festival_portal_v2_5.js", "portal/_home_feed.html"],
        "app/templates/portal/_home_feed.html": ["BYS360_HOME_FESTIVAL_PORTAL_V2_5_BEGIN", "Tarihi Alan Hava Durumu", "Kurumsal Yayın Akışı", "Öne Çıkanlar", "Aktif Gruplar", "Son Etkileşimler"],
        "app/static/css/bys360_home_festival_portal_v2_5.css": ["home-festival-portal-v25", "home-festival-video-frame", "@media"],
        "app/static/js/bys360_home_festival_portal_v2_5.js": ["BYS360_HOME_FESTIVAL_PORTAL_V2_5_BEGIN"],
        "app/services/portal_service.py": ["portal_home_featured", "portal_home_stats", "portal_recent_interactions"],
    }
    for rel, needles in required.items():
        path = project_root / rel
        if not path.exists():
            print(f"BYS360_HOME_FESTIVAL_PORTAL_V2_5_QUALITY_FAIL: eksik dosya {rel}")
            return 1
        text = read(path)
        for needle in needles:
            if needle not in text:
                print(f"BYS360_HOME_FESTIVAL_PORTAL_V2_5_QUALITY_FAIL: {rel} içinde eksik ifade: {needle}")
                return 1
    print("BYS360_HOME_FESTIVAL_PORTAL_V2_5_QUALITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
