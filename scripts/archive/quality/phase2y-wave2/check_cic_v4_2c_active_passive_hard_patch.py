from __future__ import annotations
import argparse
from pathlib import Path

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root', required=True); args=ap.parse_args()
    root=Path(args.project_root)
    cic_base=root/'app/templates/corporate_information_center/base.html'
    app_base=root/'app/templates/base.html'
    errors=[]
    c=cic_base.read_text(encoding='utf-8-sig') if cic_base.exists() else ''
    b=app_base.read_text(encoding='utf-8-sig') if app_base.exists() else ''
    if 'Aktif / Pasif' not in c: errors.append('Aktif / Pasif wording missing from corporate information base')
    for bad in ['Pilot önce','pilot önce','Pilot test yap','pilot test yap','kuru çalışma','Kuru çalışma']:
        if bad in c: errors.append(f'Old wording remains in corporate information base: {bad}')
    if 'corporate_information_center_v4_2c_active_passive.css' not in c and 'corporate_information_center_v4_2c_active_passive.css' not in b: errors.append('V4.2C css ref missing')
    if 'corporate_information_center_v4_2c_sidebar_active_passive.js' not in c and 'corporate_information_center_v4_2c_sidebar_active_passive.js' not in b: errors.append('V4.2C js ref missing')
    if errors:
        print('BYS360_CIC_V4_2C_ACTIVE_PASSIVE_HARD_PATCH_CHECK_FAIL')
        for e in errors: print('ERROR=', e)
        return 2
    print('BYS360_CIC_V4_2C_ACTIVE_PASSIVE_HARD_PATCH_CHECK_OK')
    return 0
if __name__ == '__main__': raise SystemExit(main())
