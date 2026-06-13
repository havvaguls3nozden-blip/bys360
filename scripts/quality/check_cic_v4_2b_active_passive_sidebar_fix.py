from __future__ import annotations
import argparse
from pathlib import Path
import sys

def read(path):
    return path.read_text(encoding='utf-8-sig') if path.exists() else ''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--project-root', default='.')
    args=ap.parse_args()
    root=Path(args.project_root)
    errors=[]
    base=read(root/'app/templates/base.html')
    cicbase=read(root/'app/templates/corporate_information_center/base.html')
    if 'corporate_information_center_v4_2b_active_passive_sidebar.css' not in base:
        errors.append('base.html missing v4.2b css ref')
    if 'corporate_information_center_v4_2b_active_passive_sidebar.js' not in base:
        errors.append('base.html missing v4.2b js ref')
    if '/dashboard/kurumsal-bilgilendirme/kutlamalar' not in (base + cicbase):
        errors.append('Kutlamalar link missing in template refs')
    bad_terms=[]
    for term in ['Pilot önce','pilot önce','Kuru çalışma','kuru çalışma','Pilot test yap']:
        if term in cicbase:
            bad_terms.append(term)
    if bad_terms:
        errors.append('remaining old wording: ' + ', '.join(bad_terms))
    if 'Aktif / Pasif' not in cicbase and 'Aktif/Pasif' not in cicbase:
        errors.append('Aktif / Pasif wording missing from corporate information base')
    if errors:
        print('BYS360_CIC_V4_2B_ACTIVE_PASSIVE_SIDEBAR_CHECK_FAIL')
        for e in errors: print('ERROR=', e)
        return 1
    print('BYS360_CIC_V4_2B_ACTIVE_PASSIVE_SIDEBAR_CHECK_OK')
    return 0
if __name__=='__main__':
    sys.exit(main())
