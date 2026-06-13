from __future__ import annotations

import argparse
from pathlib import Path


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root)
    errors: list[str] = []

    cic_base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    global_base = root / "app" / "templates" / "base.html"
    bad_script = root / "scripts" / "communication" / "repair_cic_v4_2c_active_passive_hard_patch.py"

    cic = read(cic_base)
    glob = read(global_base)
    bad = read(bad_script)

    if "Aktif / Pasif" not in cic:
        errors.append("Aktif / Pasif wording missing from corporate information base")
    if "Pilot önce" in cic or ">Önce<" in cic:
        errors.append("old Pilot/Once wording still visible in corporate information base")
    if "Pilot test yap" in cic:
        errors.append("Pilot test yap wording still visible")
    if "kuru çalışma" in cic.lower():
        errors.append("kuru çalışma wording still visible")
    if "corporate_information_center_v4_2d_active_passive.css" not in cic and "corporate_information_center_v4_2d_active_passive.css" not in glob:
        errors.append("V4.2D css ref missing")
    if "corporate_information_center_v4_2d_active_passive.js" not in cic and "corporate_information_center_v4_2d_active_passive.js" not in glob:
        errors.append("V4.2D js ref missing")
    if "tab='  <a class=\"{{ 'active'" in bad:
        errors.append("broken V4.2C quote syntax still present")

    if errors:
        print("BYS360_CIC_V4_2D_ACTIVE_PASSIVE_SYNTAX_FIX_CHECK_FAIL")
        for e in errors:
            print("ERROR=", e)
        return 1

    print("BYS360_CIC_V4_2D_ACTIVE_PASSIVE_SYNTAX_FIX_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
