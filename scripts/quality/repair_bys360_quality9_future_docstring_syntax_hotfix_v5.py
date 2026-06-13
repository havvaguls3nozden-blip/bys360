from __future__ import annotations

import argparse
import json
from pathlib import Path

PACKAGE = "BYS360_QUALITY9_FUTURE_DOCSTRING_SYNTAX_HOTFIX_V5_RETIRED"


def main() -> int:
    parser = argparse.ArgumentParser(description="Retired BYS360 V5 hotfix wrapper.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode", default="all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    payload = {
        "package": PACKAGE,
        "ok": True,
        "status": "retired_superseded_by_v6_v7_v8",
        "project_root": str(root),
        "mode": args.mode,
        "dry_run": bool(args.dry_run),
        "changed_count": 0,
        "finding_count": 0,
        "note": "This wrapper replaces the broken V5 repair script so compileall can pass. Use V6/V7/V8 scripts for actual repair.",
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
