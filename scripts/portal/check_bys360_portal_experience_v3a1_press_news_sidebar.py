# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path

PACKAGE = "BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_SIDEBAR"

REQUIRED = {
    "app/templates/base.html": ["BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_SIDEBAR", "portal_press_news_visible", "Basında Tarihi Alan"],
    "app/templates/portal/_tabs.html": ["BYS360_PORTAL_EXPERIENCE_V3A1_PRESS_NEWS_TAB", "Basında Tarihi Alan"],
    "app/menu_registry_data_sections.py": ["portal_press_news", "main.portal_press_news_review"],
    "app/menu_registry_data_performance.py": ["portal_press_news"],
    "app/main_handlers/account_communication_helpers.py": ["portal_press_news", "Basında Tarihi Alan Haber Onayı"],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    findings = []
    for rel, markers in REQUIRED.items():
        path = root / rel
        if not path.exists():
            findings.append({"file": rel, "issue": "missing"})
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                findings.append({"file": rel, "issue": f"marker_missing:{marker}"})
    for rel in [
        "scripts/portal/check_bys360_portal_experience_v3a1_press_news_sidebar.py",
        "scripts/portal/repair_bys360_portal_experience_v3a1_press_news_sidebar.py",
        "app/menu_registry_data_sections.py",
        "app/menu_registry_data_performance.py",
        "app/main_handlers/account_communication_helpers.py",
    ]:
        path = root / rel
        if path.exists() and path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                findings.append({"file": rel, "issue": "compile_error", "error": str(exc)})
    result = {"package": PACKAGE, "ok": not findings, "finding_count": len(findings), "findings": findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
