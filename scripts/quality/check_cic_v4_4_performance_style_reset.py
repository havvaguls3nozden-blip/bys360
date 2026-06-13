from __future__ import annotations
import argparse
from pathlib import Path
MARK = "BYS360_CIC_V4_4_PERFORMANCE_STYLE_RESET"
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--project-root", default="C:/bys360/project"); args=ap.parse_args(); root=Path(args.project_root)
    errors=[]
    cic_base=read(root/"app/templates/corporate_information_center/base.html"); global_base=read(root/"app/templates/base.html")
    css=read(root/"app/static/css/corporate_information_center_v4_4_performance_style.css"); js=read(root/"app/static/js/corporate_information_center_v4_4_active_cleanup.js")
    if "corporate_information_center_v4_4_performance_style.css" not in cic_base: errors.append("CIC base V4.4 css ref missing")
    if "corporate_information_center_v4_4_active_cleanup.js" not in cic_base and "corporate_information_center_v4_4_active_cleanup.js" not in global_base: errors.append("V4.4 js ref missing")
    if "Aktif / Pasif" not in cic_base: errors.append("Aktif / Pasif missing")
    if "Pilot önce" in cic_base or "Pilot test yap" in cic_base or "kuru çalışma" in cic_base: errors.append("legacy pilot/kuru wording remains in CIC base")
    if "cic-v41b-topbar" in cic_base or "cic-v41b-tabs" in cic_base: errors.append("legacy injected topbar/tabs marker remains in CIC base")
    if "bys360-cic-v44" not in css: errors.append("V4.4 css body scope missing")
    if "syncActive" not in js: errors.append("V4.4 active cleanup js missing syncActive")
    if "Genel Bakış', current_path.startswith('/dashboard/kurumsal-bilgilendirme')" in global_base: errors.append("global sidebar overview still broad-startswith active")
    if "/dashboard/kurumsal-bilgilendirme/kutlamalar" not in global_base: errors.append("global sidebar celebrations link missing")
    if errors:
        print(MARK+"_CHECK_FAIL")
        for e in errors: print("ERROR="+e)
        return 1
    print(MARK+"_CHECK_OK"); return 0
if __name__ == "__main__": raise SystemExit(main())
