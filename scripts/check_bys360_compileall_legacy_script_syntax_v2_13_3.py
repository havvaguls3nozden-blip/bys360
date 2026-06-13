# -*- coding: utf-8 -*-
"""BYS360_COMPILEALL_LEGACY_SCRIPT_FIX_V2_13_3 kontrol scripti."""
from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

VERSION = "BYS360_COMPILEALL_LEGACY_SCRIPT_FIX_V2_13_3"
FILES = [
    Path("scripts/repair_bys360_portal_delete_route_dedupe_v2_10_1.py"),
    Path("scripts/repair_bys360_portal_profile_me_link_v2_10_4.py"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    missing = []
    for rel in FILES:
        path = project_root / rel
        if not path.exists():
            missing.append(str(rel))
            continue
        py_compile.compile(str(path), doraise=True)
        text = path.read_text(encoding="utf-8", errors="replace")
        if VERSION not in text:
            raise SystemExit(f"Beklenen güvenli arşiv işareti yok: {rel}")

    if missing:
        print("Atlanan eski scriptler: " + ", ".join(missing))

    print(f"{VERSION}_GATE_OK")


if __name__ == "__main__":
    main()
