# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    checks = [
        (root/"app/templates/portal/people.html", "people-premium-v210"),
        (root/"app/templates/portal/people.html", "Duvarına Yaz"),
        (root/"app/static/css/bys360_portal.css", "BYS360_PORTAL_PEOPLE_PREMIUM_V2_10_CSS"),
        (root/"app/templates/portal/_post_card.html", "portal-post-delete-form-v210"),
        (root/"app/portal/routes.py", "def portal_post_delete"),
        (root/"app/portal/routes.py", 'post.status = "deleted"'),
        (root/"app/services/portal_service.py", "is_portal_post_removed"),
        (root/"app/services/portal_service.py", "ENRICH_SKIP_REMOVED"),
    ]
    failures = []
    for path, needle in checks:
        if not path.exists():
            failures.append(f"{path} bulunamadı")
            continue
        text = read(path)
        if needle not in text:
            failures.append(f"{path.name}: {needle} yok")

    routes = read(root/"app/portal/routes.py") if (root/"app/portal/routes.py").exists() else ""
    if "@bp.route" in routes or "@bp.post" in routes:
        failures.append("routes.py içinde @bp.* kaldı")
    service = read(root/"app/services/portal_service.py") if (root/"app/services/portal_service.py").exists() else ""
    if "can_user_delete_post(current_user, post)" in service or "can_user_delete_post(viewer, post)" in service:
        failures.append("portal_service.py içinde hatalı current_user/viewer silme çağrısı kaldı")

    # Visible technical expressions should not be present in people page.
    people = read(root/"app/templates/portal/people.html") if (root/"app/templates/portal/people.html").exists() else ""
    for bad in ("endpoint", "traceback", "debug", "workflow", "phase", "sync"):
        if bad in people.lower():
            failures.append(f"people.html içinde teknik ifade var: {bad}")

    if failures:
        print("BYS360_PORTAL_PEOPLE_PREMIUM_V2_10_GATE_FAIL")
        for failure in failures:
            print(f" - {failure}")
        return 1
    print("BYS360_PORTAL_PEOPLE_PREMIUM_V2_10_GATE_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
