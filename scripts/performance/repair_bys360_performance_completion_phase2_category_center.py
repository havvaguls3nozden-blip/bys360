# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "seed", "all"], default="all")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    result = {
        "package": "performance_completion_phase2_category_center",
        "version": "V1",
        "project_root": str(root),
        "mode": args.mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    sys.path.insert(0, str(root))

    if args.mode in {"seed", "all"}:
        try:
            from app import create_app
            from app.services.performance.phase2_category_center import seed_phase2_category_center

            app = create_app()
            with app.app_context():
                result["seed"] = seed_phase2_category_center(commit=True)
        except Exception as exc:
            result["seed"] = {"ok": False, "error": str(exc)}
    else:
        result["seed"] = {"ok": True, "skipped": True}

    check_script = root / "scripts" / "performance" / "check_bys360_performance_completion_phase2_category_center.py"
    cmd = [sys.executable, str(check_script), "--project-root", str(root)]
    if args.mode in {"seed", "all"}:
        cmd.append("--app-check")
    proc = subprocess.run(cmd, text=True, capture_output=True)
    result["check_exit_code"] = proc.returncode
    result["check_stdout"] = proc.stdout
    result["check_stderr"] = proc.stderr
    result["ok"] = bool(result.get("seed", {}).get("ok")) and proc.returncode == 0

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ok"]:
        print("BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER_APPLY_OK")
        return 0
    print("BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER_APPLY_FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
