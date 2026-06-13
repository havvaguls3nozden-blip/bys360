# -*- coding: utf-8 -*-
from __future__ import annotations

import py_compile
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    routes = project_root / "app" / "portal" / "routes.py"
    card = project_root / "app" / "templates" / "portal" / "_post_card.html"

    errors = []

    if not routes.exists():
        errors.append("app/portal/routes.py bulunamadı")
    else:
        text = routes.read_text(encoding="utf-8")
        delete_defs = sum(1 for line in text.splitlines() if line.lstrip().startswith("def portal_post_delete("))
        if delete_defs != 1:
            errors.append(f"portal_post_delete fonksiyonu tek olmalı; bulunan={delete_defs}")
        if '@bp.route("/portal/posts/<int:post_id>/delete"' in text or "@bp.route('/portal/posts/<int:post_id>/delete'" in text:
            errors.append("silme route'u @bp ile kalmış")
        if "/portal/posts/<int:post_id>/delete" not in text:
            errors.append("silme route adresi bulunamadı")
        try:
            py_compile.compile(str(routes), doraise=True)
        except Exception as exc:
            errors.append(f"routes.py compile hatası: {exc}")

    service = project_root / "app" / "services" / "portal_service.py"
    if service.exists():
        try:
            py_compile.compile(str(service), doraise=True)
        except Exception as exc:
            errors.append(f"portal_service.py compile hatası: {exc}")

    if card.exists():
        card_text = card.read_text(encoding="utf-8")
        if "portal-delete-post" not in card_text and "Yayından Kaldır" not in card_text and "Sil" not in card_text:
            errors.append("_post_card.html içinde silme aksiyonu görünmüyor")

    if errors:
        print("BYS360_PORTAL_DELETE_ROUTE_DEDUPE_V2_10_2_GATE_FAIL")
        for err in errors:
            print(f" - {err}")
        return 1

    print("BYS360_PORTAL_DELETE_ROUTE_DEDUPE_V2_10_2_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
