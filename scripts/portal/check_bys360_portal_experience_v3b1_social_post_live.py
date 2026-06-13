# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path

PACKAGE = "BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_POST_LIVE"
REQUIRED = {
    "app/templates/base.html": ["BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_SIDEBAR", "portal_social_import_visible", "Sosyal Medya Gönderisi Ekle"],
    "app/templates/portal/_tabs.html": ["BYS360_PORTAL_EXPERIENCE_V3B1_SOCIAL_IMPORT_TAB", "Sosyal Medya Gönderisi"],
    "app/templates/portal/social_import_v3b.html": ["Sosyal Medya Gönderisi Ekle", "Yayın Akışına Ekle", "normal portal paylaşımı"],
    "app/static/css/bys360_portal_experience_v3b1_social_post_live.css": ["social-post-live-v3b1-shell"],
}
OPTIONAL = {
    "app/menu_registry_data_sections.py": ["portal_social_import", "main.portal_social_import"],
    "app/menu_registry_data_performance.py": ["portal_social_import"],
    "app/main_handlers/account_communication_helpers.py": ["portal_social_import", "Sosyal Medya Gönderisi Ekleme"],
}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--project-root", required=True); args = parser.parse_args()
    root = Path(args.project_root).resolve(); findings = []
    for rel, markers in {**REQUIRED, **OPTIONAL}.items():
        path = root / rel
        if not path.exists():
            if rel in REQUIRED:
                findings.append({"file": rel, "issue": "missing"})
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                findings.append({"file": rel, "issue": "marker_missing", "marker": marker})
    for rel in ["scripts/portal/check_bys360_portal_experience_v3b1_social_post_live.py", "scripts/portal/repair_bys360_portal_experience_v3b1_social_post_live.py"]:
        path = root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                findings.append({"file": rel, "issue": "compile_error", "error": str(exc)})
    result = {"package": PACKAGE, "ok": not findings, "finding_count": len(findings), "findings": findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
