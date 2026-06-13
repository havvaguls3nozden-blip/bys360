# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from pathlib import Path

MARKER_BEGIN = "/* BYS360_PORTAL_INSTAGRAM_HIDE_V2_11_7_BEGIN */"
REQUIRED_ENV = {
    "BYS360_INSTAGRAM_SYNC_ENABLED": "false",
    "BYS360_INSTAGRAM_STORIES_ENABLED": "false",
    "BYS360_INSTAGRAM_FEATURE_HOME": "false",
}


def parse_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
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

    print("BYS360 Portal Instagram Feed V2.11.7 hide check basliyor...")
    print(f"ProjectRoot={project_root}")

    errors: list[str] = []
    env = parse_env(project_root / ".env")
    for key, expected in REQUIRED_ENV.items():
        if env.get(key, "").lower() != expected:
            errors.append(f".env {key} {expected} değil")

    css_candidates = [
        project_root / "app" / "static" / "css" / "bys360_portal.css",
        project_root / "app" / "static" / "css" / "portal.css",
        project_root / "static" / "css" / "bys360_portal.css",
        project_root / "static" / "css" / "portal.css",
    ]
    css_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in css_candidates if p.exists())
    if MARKER_BEGIN not in css_text:
        errors.append("CSS hide marker bulunamadı")
    if "data-source=\"instagram\"" not in css_text and "data-source=\"instagram\"" not in css_text:
        errors.append("Instagram data-source selector bulunamadı")
    if "portal-instagram-story-strip" not in css_text:
        errors.append("Story hide selector bulunamadı")

    if errors:
        print("BYS360_PORTAL_INSTAGRAM_FEED_V2_11_7_HIDE_GATE_FAIL")
        for err in errors:
            print(f" - {err}")
        return 1

    print("BYS360_PORTAL_INSTAGRAM_FEED_V2_11_7_HIDE_GATE_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
