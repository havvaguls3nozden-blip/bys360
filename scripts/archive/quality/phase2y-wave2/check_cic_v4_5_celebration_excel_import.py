
from __future__ import annotations
import argparse
from pathlib import Path
MARK='BYS360_CIC_V4_5_CELEBRATION_EXCEL_IMPORT'
CSS_NAME='corporate_information_center_v4_5_excel_import.css'
JS_NAME='corporate_information_center_v4_5_excel_import.js'

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--project-root", default="C:/bys360/project"); args=ap.parse_args(); root=Path(args.project_root)
    errors=[]
    service=read(root/"app/services/corporate_information_center.py")
    routes=read(root/"app/communication/corporate_information_center_routes.py")
    base=read(root/"app/templates/corporate_information_center/base.html")
    celebrations=read(root/"app/templates/corporate_information_center/celebrations.html")
    system=read(root/"app/templates/corporate_information_center/system.html")
    css=read(root/"app/static/css"/CSS_NAME)
    js=read(root/"app/static/js"/JS_NAME)
    if "import_celebration_dates_from_excel" not in service: errors.append("service import function missing")
    if "excel-yukle" not in routes or "excel-sablon" not in routes: errors.append("excel upload/template routes missing")
    if CSS_NAME not in base: errors.append("V4.5 css ref missing from base")
    if JS_NAME not in base: errors.append("V4.5 js ref missing from base")
    if "Excel ile Personel Kutlama Tarihleri Yükle" not in celebrations: errors.append("Excel upload panel missing from celebrations page")
    if "#excel-yukleme" not in system: errors.append("System page excel upload shortcut missing")
    if "cic-v45-excel-upload" not in css: errors.append("V4.5 excel css missing")
    if "bys360-cic-v45" not in js: errors.append("V4.5 js marker missing")
    if errors:
        print(MARK + "_CHECK_FAIL")
        for e in errors: print("ERROR=" + e)
        return 1
    print(MARK + "_CHECK_OK")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
