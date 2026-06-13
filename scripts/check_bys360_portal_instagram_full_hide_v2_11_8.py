# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

REQUIRED_ENV = {
    "BYS360_INSTAGRAM_SYNC_ENABLED": "false",
    "BYS360_INSTAGRAM_STORIES_ENABLED": "false",
    "BYS360_INSTAGRAM_FEATURE_HOME": "false",
    "BYS360_INSTAGRAM_FEATURE_PORTAL": "false",
    "BYS360_INSTAGRAM_VISIBLE": "false",
}
CSS_MARKER = "BYS360_PORTAL_INSTAGRAM_FULL_HIDE_V2_11_8_BEGIN"
POSTCARD_MARKER = "BYS360_PORTAL_INSTAGRAM_FULL_HIDE_V2_11_8_POSTCARD_BEGIN"
HOME_MARKER = "BYS360_PORTAL_INSTAGRAM_FULL_HIDE_V2_11_8_HOME_CLASSES"


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_env(path: Path) -> dict[str, str]:
    data = {}
    for raw in read(path).splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        data[k.strip()] = v.strip()
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    print("BYS360 Portal Instagram Feed V2.11.8 full hide check basliyor...")
    print(f"ProjectRoot={project_root}")

    errors: list[str] = []
    env = parse_env(project_root / ".env")
    for k, expected in REQUIRED_ENV.items():
        if env.get(k, "").lower() != expected:
            errors.append(f".env {k}={expected} değil")

    feed = read(project_root / "app" / "templates" / "portal" / "feed.html")
    home = read(project_root / "app" / "templates" / "portal" / "_home_feed.html")
    post_card = read(project_root / "app" / "templates" / "portal" / "_post_card.html")
    css = "\n".join(read(p) for p in [
        project_root / "app" / "static" / "css" / "bys360_portal.css",
        project_root / "app" / "static" / "css" / "portal.css",
        project_root / "static" / "css" / "bys360_portal.css",
        project_root / "static" / "css" / "portal.css",
    ])

    if "portal-instagram-sync-card" in feed:
        errors.append("Portal sağ Instagram akışı kartı feed.html içinde hâlâ var")
    if "portal-instagram-story-strip" in feed:
        errors.append("Portal story şeridi feed.html içinde hâlâ var")
    if "home-v251-instagram-stories" in home:
        errors.append("Anasayfa Instagram story kartı _home_feed.html içinde hâlâ var")
    if HOME_MARKER not in home and "bys360-instagram-hidden-source" not in home:
        errors.append("Anasayfa Instagram kaynaklı post class filtresi yok")
    if POSTCARD_MARKER not in post_card:
        errors.append("Portal post kartında Instagram kaynak filtresi yok")
    if CSS_MARKER not in css:
        errors.append("Full hide CSS marker yok")
    if "portal-instagram-sync-card" not in css or "home-v251-instagram-stories" not in css:
        errors.append("CSS anasayfa/sağ kart gizleme seçicileri eksik")

    if errors:
        print("BYS360_PORTAL_INSTAGRAM_FEED_V2_11_8_FULL_HIDE_GATE_FAIL")
        for e in errors:
            print(f" - {e}")
        return 1
    print("BYS360_PORTAL_INSTAGRAM_FEED_V2_11_8_FULL_HIDE_GATE_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
