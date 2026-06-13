# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path
PACKAGE = "BYS360_PORTAL_EXPERIENCE_V1B_GUARD"
REQUIRED = ["app/services/portal_experience_service.py", "app/templates/portal/_experience_dashboard.html", "app/static/css/bys360_portal_experience_v1.css", "app/main_handlers/public_handlers.py", "app/portal/routes.py", "app/templates/home.html", "app/templates/portal/feed.html"]
PY_FILES = ["app/services/portal_experience_service.py", "app/main_handlers/public_handlers.py", "app/portal/routes.py"]
MARKERS = [("app/services/portal_experience_service.py", "Portal Deneyimi V1B"), ("app/templates/portal/_experience_dashboard.html", "BYS360_PORTAL_EXPERIENCE_V1B_BEGIN"), ("app/static/css/bys360_portal_experience_v1.css", "BYS360 Portal Deneyimi V1B"), ("app/main_handlers/public_handlers.py", "portal_experience_context(current_user)"), ("app/portal/routes.py", "portal_experience_context(current_user)")]
def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--project-root", required=True); args = parser.parse_args(); root = Path(args.project_root).resolve(); findings = []
    for rel in REQUIRED:
        if not (root / rel).exists(): findings.append({"type": "missing", "file": rel})
    for rel in PY_FILES:
        path = root / rel
        if path.exists():
            try: py_compile.compile(str(path), doraise=True)
            except Exception as exc: findings.append({"type": "compile", "file": rel, "error": str(exc)})
    for rel, marker in MARKERS:
        path = root / rel
        if path.exists() and marker not in path.read_text(encoding="utf-8", errors="ignore"): findings.append({"type": "marker", "file": rel, "marker": marker})
    result = {"package": PACKAGE, "ok": not findings, "finding_count": len(findings), "findings": findings}; print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if not findings else 1
if __name__ == "__main__": raise SystemExit(main())
