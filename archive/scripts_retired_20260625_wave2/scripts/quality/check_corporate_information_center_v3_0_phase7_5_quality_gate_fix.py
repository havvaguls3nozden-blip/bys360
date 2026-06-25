# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

GATE = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_5_QUALITY_GATE_FIX_GATE_OK"
FINAL = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_5_QUALITY_GATE_FIX_FINAL_OK"

BAD_FRAGMENTS = [
    "expected token",
    "unterminated string literal",
    "unexpected character after line continuation character",
    ">') }}",
    "2_15_18\">')",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default="C:/bys360/project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)

    quality_74 = root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_4_release_pro_ui.py"
    quality_75 = root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_5_quality_gate_fix.py"
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    system = root / "app" / "templates" / "corporate_information_center" / "system.html"

    errors = []
    for p in [quality_74, quality_75, base, system]:
        if not p.exists():
            errors.append(f"eksik dosya: {p}")

    if not errors:
        for p in [quality_74, quality_75]:
            try:
                py_compile.compile(str(p), doraise=True)
            except Exception as exc:
                errors.append(f"Python sözdizimi hatası: {p.name}: {exc}")

        base_text = read_text(base)
        for marker in [
            "corporate_information_center_v3_0_phase7.css",
            "corporate_information_center_v3_0_phase7_4_release_pro.css",
        ]:
            if marker not in base_text:
                errors.append(f"base.html içinde eksik CSS bağlantısı: {marker}")

        for bad in BAD_FRAGMENTS:
            if bad in base_text:
                errors.append(f"base.html içinde bozuk kalıntı: {bad}")

    if errors:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_5_QUALITY_GATE_FIX_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 2

    print(GATE)
    print(FINAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
