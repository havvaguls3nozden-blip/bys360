from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path
VERSION="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE1"
def main():
    p=argparse.ArgumentParser(); p.add_argument('--project-root', default='.')
    root=Path(p.parse_args().project_root)
    errors=[]
    required=[
        'app/services/corporate_information_center.py',
        'app/communication/corporate_information_center_routes.py',
        'app/templates/corporate_information_center/overview.html',
        'app/templates/corporate_information_center/tasks.html',
        'app/templates/corporate_information_center/recipients.html',
        'app/templates/corporate_information_center/templates.html',
        'app/templates/corporate_information_center/test.html',
        'app/templates/corporate_information_center/logs.html',
        'app/templates/corporate_information_center/system.html',
        'scripts/communication/run_corporate_information_task.py',
        'scripts/windows/install_bys360_corporate_information_tasks_v3_0.ps1',
    ]
    for r in required:
        if not (root/r).exists(): errors.append(f'eksik: {r}')
    for r in ['app/services/corporate_information_center.py','app/communication/corporate_information_center_routes.py','scripts/communication/run_corporate_information_task.py','app/routes.py']:
        try: py_compile.compile(str(root/r), doraise=True)
        except Exception as exc: errors.append(f'compile hata: {r}: {exc}')
    routes=(root/'app/routes.py').read_text(encoding='utf-8', errors='ignore') if (root/'app/routes.py').exists() else ''
    if 'corporate_information_center_routes' not in routes: errors.append('app/routes.py yeni route import yok')
    base=(root/'app/templates/base.html').read_text(encoding='utf-8', errors='ignore') if (root/'app/templates/base.html').exists() else ''
    if '/dashboard/kurumsal-bilgilendirme' not in base: errors.append('base menüde Kurumsal Bilgilendirme Merkezi yok')
    if 'Yönetici Özeti</span>' in base or 'Günlük Personel Bilgilendirme' in base: errors.append('eski yönetici özeti/günlük bilgilendirme menüsü hâlâ görünüyor')
    print(json.dumps({'ok': not errors, 'version': VERSION, 'errors': errors}, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(1)
    print(VERSION+'_CHECK_OK')
if __name__=='__main__': main()
