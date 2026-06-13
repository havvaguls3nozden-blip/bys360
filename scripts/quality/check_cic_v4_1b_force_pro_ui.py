from __future__ import annotations

import argparse
import re
from pathlib import Path

REQUIRED = [
    "scripts/windows/repair_cic_v4_1b_force_pro_ui.ps1",
    "scripts/communication/repair_cic_v4_1b_force_pro_ui.py",
    "app/static/css/corporate_information_center_v4_1b_force_pro.css",
    "app/static/js/corporate_information_center_v4_1b_force_pro.js",
]

MARKER = "BYS360_CIC_V4_1B_FORCE_PRO_UI"


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    missing = [p for p in REQUIRED if not (root / p).exists()]
    if missing:
        print("MISSING_FILES=", missing)
        return 2

    css = read_text(root / "app/static/css/corporate_information_center_v4_1b_force_pro.css")
    js = read_text(root / "app/static/js/corporate_information_center_v4_1b_force_pro.js")
    if MARKER not in css or MARKER not in js:
        print("MARKER_MISSING")
        return 3

    template_root = root / "app" / "templates"
    found_asset_ref = False
    for candidate in [template_root / "base.html", template_root / "layout.html", template_root / "corporate_information_center" / "base.html"]:
        if candidate.exists():
            txt = read_text(candidate)
            if "corporate_information_center_v4_1b_force_pro" in txt:
                found_asset_ref = True
                break
    if not found_asset_ref:
        # CIC individual pages may be patched as fallback.
        for path in (template_root / "corporate_information_center").glob("*.html") if (template_root / "corporate_information_center").exists() else []:
            if "corporate_information_center_v4_1b_force_pro" in read_text(path):
                found_asset_ref = True
                break
    if not found_asset_ref:
        print("ASSET_REFERENCE_NOT_FOUND_IN_TEMPLATES")
        return 4

    pilot_hits = []
    if (template_root / "corporate_information_center").exists():
        for path in (template_root / "corporate_information_center").glob("*.html"):
            txt = read_text(path)
            # Ignore URLs/filenames/technical identifiers less; report all for human check.
            if re.search(r"\bpilot\b", txt, flags=re.I):
                pilot_hits.append(str(path.relative_to(root)))
    if pilot_hits:
        print("PILOT_TEXT_STILL_FOUND=", pilot_hits)
        return 5

    print("BYS360_CIC_V4_1B_FORCE_PRO_UI_CHECK_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
