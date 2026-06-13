from __future__ import annotations
import argparse
from pathlib import Path

TAB = "/dashboard/kurumsal-bilgilendirme/kutlamalar"

def read(p):
    return p.read_text(encoding="utf-8-sig") if p.exists() else ""

parser=argparse.ArgumentParser()
parser.add_argument("--project-root", required=True)
args=parser.parse_args()
root=Path(args.project_root)
base=root/"app/templates/corporate_information_center/base.html"
cele=root/"app/templates/corporate_information_center/celebrations.html"
errors=[]
text=read(base)
if TAB not in text:
    errors.append("Kutlamalar sekmesi corporate_information_center/base.html içinde yok.")
if "active=='celebrations'" not in text:
    errors.append("Kutlamalar sekmesi active state kontrolü yok.")
ct=read(cele)
if "active_tab='celebrations'" not in ct and 'active_tab="celebrations"' not in ct:
    errors.append("celebrations.html active_tab='celebrations' değil.")
if errors:
    print("BYS360_CIC_V4_0A_MENU_TAB_FIX_CHECK_FAIL")
    for e in errors: print("-", e)
    raise SystemExit(1)
print("BYS360_CIC_V4_0A_MENU_TAB_FIX_CHECK_OK")
