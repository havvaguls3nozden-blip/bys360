# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

GATE = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_6_QUALITY_SCRIPT_REPAIR_GATE_OK"
FINAL = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_6_QUALITY_SCRIPT_REPAIR_FINAL_OK"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default="C:/bys360/project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)

    files = [
        root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_4_release_pro_ui.py",
        root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_5_quality_gate_fix.py",
        root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
        root / "scripts" / "communication" / "repair_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
    ]
    errors = []
    for path in files:
        if not path.exists():
            errors.append(f"eksik dosya: {path}")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append(f"Python sözdizimi hatası: {path.name}: {exc}")

    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    if base.exists():
        text = base.read_text(encoding="utf-8", errors="ignore")
        if "corporate_information_center_v3_0_phase7.css" not in text:
            errors.append("base.html phase7 css bağlantısı eksik")
        if "corporate_information_center_v3_0_phase7_4_release_pro.css" not in text:
            errors.append("base.html phase7_4 release css bağlantısı eksik")
        for bad in [">') }}", "2_15_18\">')", "expected token", "unterminated string"]:
            if bad in text:
                errors.append(f"base.html içinde bozuk kalıntı var: {bad}")
    else:
        errors.append(f"eksik dosya: {base}")

    if errors:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_6_QUALITY_SCRIPT_REPAIR_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 2

    print(GATE)
    print(FINAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
