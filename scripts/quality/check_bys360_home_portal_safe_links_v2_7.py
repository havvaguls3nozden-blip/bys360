from __future__ import annotations
import sys
from pathlib import Path

MARKER = "BYS360_HOME_PORTAL_SAFE_LINKS_V2_7"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    feed = root / "app" / "templates" / "portal" / "_home_feed.html"
    require(feed.exists(), "app/templates/portal/_home_feed.html not found")
    text = read_text(feed)
    require(MARKER in text, "Safe links marker missing")
    require("safe_url_for('main.portal_profile'" not in text and 'safe_url_for("main.portal_profile"' not in text, "portal_profile safe_url_for warning source still exists")
    require("safe_url_for('main.notifications'" not in text and 'safe_url_for("main.notifications"' not in text, "notifications safe_url_for warning source still exists")
    require("/portal/profile" in text, "direct portal profile link missing")
    require("/notifications" in text or "notifications_list" in text, "notifications link missing")
    print("BYS360_HOME_PORTAL_SAFE_LINKS_V2_7_GATE_OK")
    print("BYS360_HOME_PORTAL_SAFE_LINKS_V2_7_QUALITY_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
