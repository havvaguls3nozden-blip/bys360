from __future__ import annotations
import argparse
from pathlib import Path
MARK="BYS360_CIC_V4_3_FULL_PRO_UI_SIDEBAR_ACTIVE"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root', required=True); args=ap.parse_args()
    root=Path(args.project_root); errors=[]
    cic_base=root/'app/templates/corporate_information_center/base.html'; global_base=root/'app/templates/base.html'
    css=root/'app/static/css/corporate_information_center_v4_3_full_pro.css'; js=root/'app/static/js/corporate_information_center_v4_3_sidebar_active.js'
    if not cic_base.exists(): errors.append('corporate information base missing')
    if not css.exists(): errors.append('v4.3 css missing')
    if not js.exists(): errors.append('v4.3 js missing')
    txt=cic_base.read_text(encoding='utf-8', errors='ignore') if cic_base.exists() else ''
    if 'corporate_information_center_v4_3_full_pro.css' not in txt: errors.append('cic base missing v4.3 css ref')
    if 'corporate_information_center_v4_3_sidebar_active.js' not in txt: errors.append('cic base missing v4.3 js ref')
    if 'Aktif / Pasif' not in txt: errors.append('Aktif / Pasif wording missing')
    if 'Pilot önce' in txt or 'Pilot test yap' in txt: errors.append('old pilot wording still in cic base')
    if 'cic-v43-hero' not in txt: errors.append('v4.3 hero missing')
    if '/dashboard/kurumsal-bilgilendirme/kutlamalar' not in txt: errors.append('celebrations tab missing in cic base')
    if global_base.exists():
        g=global_base.read_text(encoding='utf-8', errors='ignore')
        if "current_path == '/dashboard/kurumsal-bilgilendirme'" not in g: errors.append('global overview active is not exact')
        if 'corporate_information_celebrations' not in g and 'corporate_information_center_v4_3_sidebar_active.js' not in g: errors.append('global sidebar celebration/js hook missing')
    if errors:
        print(MARK+'_CHECK_FAIL')
        for e in errors: print('ERROR=', e)
        raise SystemExit(1)
    print(MARK+'_CHECK_OK')
if __name__=='__main__': main()
