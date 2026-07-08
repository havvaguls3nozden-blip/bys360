from __future__ import annotations

import argparse
import compileall
import json
import os
import sys
from pathlib import Path

VERSION = "BYS36043_RESTORE_GATE_V1"

REQUIRED_FILES = [
    "app/portal/routes.py",
    "app/templates/portal/feed.html",
    "app/templates/portal/people.html",
    "app/services/portal_permission_matrix.py",
    "app/templates/base.html",
    "wsgi.py",
]
REQUIRED_MARKERS = {
    "app/portal/routes.py": ["def portal_feed", "menu_key_required(\"portal_feed\")", "portal_permission_allowed"],
    "app/services/portal_permission_matrix.py": ["PORTAL_MATRIX_KEYS", "portal_permission_allowed", "PORTAL_DEFAULTS"],
}
FORBIDDEN_NESTED_ROOTS = ["bys360/project/app", "project/app"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    args = ap.parse_args()
    project_root = Path(args.project_root).resolve()
    os.chdir(project_root)

    failures: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_FILES:
        if not (project_root / rel).exists():
            failures.append(f"Eksik dosya: {rel}")
    for rel, markers in REQUIRED_MARKERS.items():
        p = project_root / rel
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="ignore")
            for marker in markers:
                if marker not in text:
                    failures.append(f"Beklenen işaret yok: {rel} :: {marker}")

    for rel in FORBIDDEN_NESTED_ROOTS:
        if (project_root / rel).exists():
            failures.append(f"Zip yanlış klasöre açılmış görünüyor: {rel}")

    if not (project_root / ".env").exists():
        warnings.append("Canlı .env dosyası görünmüyor. Uygulama ortam değişkenleriyle çalışıyorsa sorun olmayabilir.")

    compile_targets = [str(project_root / "app")]
    for f in ("config.py", "wsgi.py"):
        if (project_root / f).exists():
            compile_targets.append(str(project_root / f))
    ok = compileall.compile_file(str(project_root / "wsgi.py"), quiet=1) if (project_root / "wsgi.py").exists() else True
    ok = compileall.compile_dir(str(project_root / "app"), quiet=1) and ok
    if not ok:
        failures.append("Python compileall başarısız oldu.")

    report = {"version": VERSION, "project_root": str(project_root), "failures": failures, "warnings": warnings}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        print(f"{VERSION}_FAIL")
        return 1
    print(f"{VERSION}_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
