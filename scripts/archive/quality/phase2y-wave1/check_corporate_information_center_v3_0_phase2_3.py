# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE2_3_CSRF_RECIPIENT_UX"

def main() -> int:
    root = Path(os.environ.get("BYS360_PROJECT_ROOT", os.getcwd())).resolve()
    script = root / "scripts" / "communication" / "repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux.py"
    if not script.exists():
        print(json.dumps({"ok": False, "error": f"Kontrol scripti bulunamadı: {script}"}, ensure_ascii=False, indent=2))
        return 2
    cmd = [sys.executable, str(script), "--project-root", str(root), "--mode", "check"]
    completed = subprocess.run(cmd, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    return completed.returncode

if __name__ == "__main__":
    raise SystemExit(main())
