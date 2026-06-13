
from __future__ import annotations
import argparse, sys
from pathlib import Path
MARK="BYS360_CIC_V4_6_CELEBRATIONS_STUDIO_PRO_UI"
CSS="corporate_information_center_v4_6_celebrations_studio.css"
JS="corporate_information_center_v4_6_celebrations_studio.js"

def read(p):
    return Path(p).read_text(encoding='utf-8', errors='ignore') if Path(p).exists() else ''

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',required=True); ns=ap.parse_args(); root=Path(ns.project_root)
    errors=[]
    base=read(root/'app/templates/corporate_information_center/base.html')
    cele=read(root/'app/templates/corporate_information_center/celebrations.html')
    if CSS not in base: errors.append('base css ref missing')
    if JS not in base: errors.append('base js ref missing')
    if MARK not in read(root/'app/static/css'/CSS): errors.append('css marker missing')
    if MARK not in read(root/'app/static/js'/JS): errors.append('js marker missing')
    if 'cic-celeb-studio' not in cele: errors.append('new celebrations template missing')
    if 'Excel ile personel kutlama tarihleri yükle' not in cele: errors.append('excel import area missing')
    if 'text-primary' in cele or 'link-primary' in cele or 'btn-link' in cele: errors.append('blue link class remains in celebrations template')
    if 'kuru çalışma' in cele or 'Pilot test' in cele or 'Pilot önce' in cele: errors.append('legacy wording remains in celebrations template')
    if errors:
        print(MARK+'_CHECK_FAIL')
        for e in errors: print('ERROR=', e)
        return 1
    print(MARK+'_CHECK_OK')
    return 0
if __name__=='__main__': sys.exit(main())
