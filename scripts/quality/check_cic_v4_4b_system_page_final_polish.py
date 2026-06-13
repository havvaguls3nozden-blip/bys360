
from __future__ import annotations
import argparse
from pathlib import Path
MARK='BYS360_CIC_V4_4B_SYSTEM_PAGE_FINAL_POLISH'
CSS_NAME='corporate_information_center_v4_4b_system_page_final.css'
JS_NAME='corporate_information_center_v4_4b_system_page_final.js'

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--project-root", default="C:/bys360/project"); args=ap.parse_args(); root=Path(args.project_root)
    errors=[]
    base=read(root/"app/templates/corporate_information_center/base.html")
    system=read(root/"app/templates/corporate_information_center/system.html")
    css=read(root/"app/static/css"/CSS_NAME)
    js=read(root/"app/static/js"/JS_NAME)
    if CSS_NAME not in base: errors.append("V4.4B css ref missing from corporate information base")
    if JS_NAME not in base: errors.append("V4.4B js ref missing from corporate information base")
    if "Kutlamaları yönet" not in system: errors.append("system page does not include styled Kutlamaları yönet action")
    if "Önizleme / test gönderimi" not in system: errors.append("system page does not include clean test wording")
    if "pilot test" in system.lower() or "Pilot test" in system: errors.append("pilot test wording still exists in system page")
    if 'cic-actions a[href*="/dashboard/kurumsal-bilgilendirme/kutlamalar"]' not in css: errors.append("CSS missing specific Kutlamalar action styling")
    if "text-primary" not in js or "link-primary" not in js: errors.append("JS missing blue link class cleanup")
    if errors:
        print(MARK + "_CHECK_FAIL")
        for e in errors: print("ERROR=" + e)
        return 1
    print(MARK + "_CHECK_OK")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
