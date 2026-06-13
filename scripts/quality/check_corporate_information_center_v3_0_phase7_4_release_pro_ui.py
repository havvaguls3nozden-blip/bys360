# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

GATE = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_4_RELEASE_PRO_UI_GATE_OK"
FINAL = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_4_RELEASE_PRO_UI_FINAL_OK"

BAD_FRAGMENTS = [
    "expected token",
    "unterminated string",
    ">') }}",
    "2_15_18\">')",
    "line continuation character",
]

REQUIRED_BASE_MARKERS = [
    "corporate_information_center_v3_0_phase7.css",
    "corporate_information_center_v3_0_phase7_4_release_pro.css",
]

REQUIRED_SYSTEM_MARKERS = [
    "release",
    "Canlı Geçiş",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default="C:/bys360/project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)

    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    system = root / "app" / "templates" / "corporate_information_center" / "system.html"
    css = root / "app" / "static" / "css" / "corporate_information_center_v3_0_phase7_4_release_pro.css"

    missing = [str(p) for p in [base, system, css] if not p.exists()]
    if missing:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_4_RELEASE_PRO_UI_GATE_FAIL")
        for item in missing:
            print(f"HATA: eksik dosya: {item}")
        return 2

    base_text = read_text(base)
    system_text = read_text(system)

    errors = []
    for marker in REQUIRED_BASE_MARKERS:
        if marker not in base_text:
            errors.append(f"base.html içinde eksik ifade: {marker}")
    for marker in REQUIRED_SYSTEM_MARKERS:
        if marker not in system_text:
            errors.append(f"system.html içinde eksik ifade: {marker}")
    for bad in BAD_FRAGMENTS:
        if bad in base_text:
            errors.append(f"base.html içinde bozuk kalıntı var: {bad}")

    try:
        py_compile.compile(str(Path(__file__)), doraise=True)
    except Exception as exc:
        errors.append(f"kalite script py_compile hatası: {exc}")

    if errors:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_4_RELEASE_PRO_UI_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 2

    print(GATE)
    print(FINAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
