from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    repair_path = root / "scripts/live/repair_bys360_live_full_overlay_v2_17_62.py"
    if not repair_path.exists():
        raise SystemExit(f"Repair script bulunamadı: {repair_path}")
    spec = importlib.util.spec_from_file_location("bys360_live_full_overlay_v2_17_62", repair_path)
    if spec is None or spec.loader is None:
        raise SystemExit("Repair script import edilemedi.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    report = module.check_project(root)
    module.write_report(root, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report.get("ok"):
        failed = [c for c in report.get("checks", []) if not c.get("ok")]
        print("\nBASARISIZ KONTROLLER:")
        for item in failed:
            print(f"- {item.get('name')}: {item.get('detail')}")
        return 2
    print("BYS360_LIVE_FULL_OVERLAY_V2_17_62_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
