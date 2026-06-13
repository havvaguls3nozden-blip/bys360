# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
import py_compile
from pathlib import Path

PACKAGE = "BYS360_PORTAL_EXPERIENCE_V1"
REQUIRED_FILES = [
    "app/services/portal_experience_service.py",
    "app/templates/portal/_experience_dashboard.html",
    "app/static/css/bys360_portal_experience_v1.css",
]
PATCH_MARKERS = {
    "app/main_handlers/public_handlers.py": ["portal_experience_context"],
    "app/portal/routes.py": ["portal_experience_context", "portal_experience_context(current_user)"],
    "app/services/portal_service.py": ["thanks", "İyi Uygulama"],
    "app/templates/home.html": ["BYS360_PORTAL_EXPERIENCE_V1_HOME_CSS", "BYS360_PORTAL_EXPERIENCE_V1_HOME_INCLUDE"],
    "app/templates/portal/feed.html": ["BYS360_PORTAL_EXPERIENCE_V1_FEED_CSS", "BYS360_PORTAL_EXPERIENCE_V1_FEED_INCLUDE"],
}
PY_COMPILE = [
    "app/services/portal_experience_service.py",
    "app/main_handlers/public_handlers.py",
    "app/portal/routes.py",
    "app/services/portal_service.py",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    findings = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            findings.append({"type": "missing_file", "file": rel})
    for rel, markers in PATCH_MARKERS.items():
        path = root / rel
        if not path.exists():
            findings.append({"type": "missing_patch_target", "file": rel})
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                findings.append({"type": "missing_marker", "file": rel, "marker": marker})
    for rel in PY_COMPILE:
        path = root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                findings.append({"type": "compile_error", "file": rel, "error": str(exc)})
    result = {"package": PACKAGE, "ok": not findings, "finding_count": len(findings), "findings": findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
