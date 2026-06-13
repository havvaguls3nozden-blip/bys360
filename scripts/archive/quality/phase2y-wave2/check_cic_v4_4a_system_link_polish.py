from __future__ import annotations
import argparse
from pathlib import Path
MARK = "BYS360_CIC_V4_4A_SYSTEM_LINK_POLISH"
CSS_NAME = "corporate_information_center_v4_4a_system_link_polish.css"
JS_NAME = "corporate_information_center_v4_4a_system_link_polish.js"
def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--project-root", default="C:/bys360/project"); args = ap.parse_args(); root = Path(args.project_root)
    errors=[]
    cic_base = read(root/"app/templates/corporate_information_center/base.html")
    css = read(root/"app/static/css"/CSS_NAME)
    js = read(root/"app/static/js"/JS_NAME)
    if CSS_NAME not in cic_base: errors.append("V4.4A css ref missing from corporate information base")
    if JS_NAME not in cic_base: errors.append("V4.4A js ref missing from corporate information base")
    if "bys360-cic-system-page" not in css: errors.append("system page css scope missing")
    if "text-primary" not in js or "link-primary" not in js: errors.append("JS does not remove bootstrap blue link classes")
    if "bys360-cic-v44a" not in js: errors.append("JS body marker missing")
    if errors:
        print(MARK + "_CHECK_FAIL")
        for e in errors: print("ERROR=" + e)
        return 1
    print(MARK + "_CHECK_OK")
    return 0
if __name__ == "__main__": raise SystemExit(main())
