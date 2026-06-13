# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import os
import py_compile
from pathlib import Path

TAG = "BYS360_PORTAL_PROFILE_WALL_V2_9_1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", "-p", default=os.environ.get("ProjectRoot") or os.getcwd())
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    service = root / "app" / "services" / "portal_service.py"
    routes = root / "app" / "portal" / "routes.py"
    errors: list[str] = []

    if not service.exists():
        errors.append("app/services/portal_service.py bulunamadı")
    else:
        text = service.read_text(encoding="utf-8")
        if "can_user_delete_post(viewer, post)" in text:
            errors.append("portal_service.py içinde hatalı viewer delete referansı kaldı")
        if "def enrich_posts" not in text:
            errors.append("portal_service.py içinde enrich_posts fonksiyonu bulunamadı")
        if "can_user_delete_post(current_user, post)" not in text:
            errors.append("portal_service.py içinde current_user delete kontrolü bulunamadı")
        try:
            py_compile.compile(str(service), doraise=True)
        except Exception as exc:
            errors.append(f"portal_service.py compile hatası: {exc}")

    if routes.exists():
        try:
            py_compile.compile(str(routes), doraise=True)
        except Exception as exc:
            errors.append(f"routes.py compile hatası: {exc}")

    if errors:
        print(f"{TAG}_GATE_FAIL")
        for err in errors:
            print(f" - {err}")
        return 1

    print(f"{TAG}_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
