# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

SIGNATURE = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_1_BASE_CSS_LINK_FIX"

def load_repair_module(root: Path):
    mod_path = root / "scripts" / "communication" / "repair_corporate_information_center_v3_0_phase7_1_base_css_link_fix.py"
    if not mod_path.exists():
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_1_BASE_CSS_LINK_FIX_GATE_FAIL")
        print(f"HATA: Onarim modulu bulunamadi: {mod_path}")
        return None
    spec = importlib.util.spec_from_file_location("phase7_1_repair", mod_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", "-ProjectRoot", dest="project_root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    module = load_repair_module(root)
    if module is None:
        return 2
    errors = module.check(root)
    if errors:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_1_BASE_CSS_LINK_FIX_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 2
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_1_BASE_CSS_LINK_FIX_GATE_OK")
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_1_BASE_CSS_LINK_FIX_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
