# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def load_module(root: Path):
    path = root / "scripts" / "communication" / "repair_corporate_information_center_v3_0_phase7_3_flat_css_link_fix.py"
    if not path.exists():
        raise FileNotFoundError(f"Onarim modulu bulunamadi: {path}")
    spec = importlib.util.spec_from_file_location("phase7_3_repair", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default="C:\\bys360\\project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot).resolve()
    module = load_module(root)
    module.gate(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
