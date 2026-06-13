# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    failures = []

    routes = root / "app" / "portal" / "routes.py"
    service = root / "app" / "services" / "portal_service.py"
    card = root / "app" / "templates" / "portal" / "_post_card.html"

    if not routes.exists() or "def portal_delete_post" not in read_text(routes):
        failures.append("routes.py icinde portal_delete_post yok")
    if routes.exists() and "/portal/posts/<int:post_id>/delete" not in read_text(routes):
        failures.append("routes.py icinde delete endpoint yolu yok")

    if not service.exists():
        failures.append("portal_service.py yok")
    else:
        s = read_text(service)
        if "def can_user_delete_post" not in s:
            failures.append("portal_service.py icinde can_user_delete_post yok")
        if "can_user_delete_post(viewer, post)" in s or "can_user_delete_post(current_user, post)" in s:
            failures.append("portal_service.py icinde hatali viewer/current_user delete cagrisi kalmis")
        if "can_user_delete_post(user, post)" not in s:
            failures.append("portal_service.py icinde user parametreli delete cagrisi yok")

    if not card.exists() or "portal-delete-post" not in read_text(card):
        failures.append("_post_card.html icinde portal-delete-post yok")

    if failures:
        print("BYS360_PORTAL_PROFILE_WALL_V2_9_4_GATE_FAIL")
        for f in failures:
            print(f" - {f}")
        return 1

    print("BYS360_PORTAL_PROFILE_WALL_V2_9_4_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
