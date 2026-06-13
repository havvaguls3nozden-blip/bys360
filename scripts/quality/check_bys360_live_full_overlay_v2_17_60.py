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
    repair_path = root / "scripts/live/repair_bys360_live_full_overlay_v2_17_60.py"
    if not repair_path.exists():
        raise SystemExit(f"Repair script bulunamadı: {repair_path}")
    spec = importlib.util.spec_from_file_location("bys360_live_full_overlay_v2_17_60", repair_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    report = module.check_project(root)
    module.write_report(root, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
