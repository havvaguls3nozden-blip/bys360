from __future__ import annotations
import sys
from pathlib import Path

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")

def main() -> int:
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    checks = {
        "app/templates/portal/_home_feed.html": ["BYS360_HOME_FESTIVAL_PORTAL_V2_5_1_BEGIN", "Yayın Akışı Özeti", "Kısa vitrin", "Son Akış"],
        "app/static/css/bys360_home_festival_portal_v2_5.css": ["BYS360_HOME_FESTIVAL_PORTAL_V2_5_1_BEGIN", "home-v251-feed-row", "@media"],
        "app/static/js/bys360_home_festival_portal_v2_5.js": ["BYS360_HOME_FESTIVAL_PORTAL_V2_5_1_BEGIN"],
    }
    for rel, needles in checks.items():
        path = project_root / rel
        if not path.exists():
            print(f"BYS360_HOME_FESTIVAL_PORTAL_V2_5_1_GATE_FAIL: eksik dosya {rel}")
            return 1
        text = read(path)
        for needle in needles:
            if needle not in text:
                print(f"BYS360_HOME_FESTIVAL_PORTAL_V2_5_1_GATE_FAIL: {rel} içinde eksik ifade: {needle}")
                return 1
    home_feed = read(project_root / "app/templates/portal/_home_feed.html")
    forbidden = ["Tarihi Alan Hava Durumu", "home-festival-weather-card", "weather-mini-icon", "home-festival-featured-row", "featured-media"]
    for item in forbidden:
        if item in home_feed:
            print(f"BYS360_HOME_FESTIVAL_PORTAL_V2_5_1_GATE_FAIL: portal alanında kaldırılması gereken ifade kaldı: {item}")
            return 1
    print("BYS360_HOME_FESTIVAL_PORTAL_V2_5_1_GATE_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
