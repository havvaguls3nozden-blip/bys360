from pathlib import Path
import argparse, json, py_compile
VERSION='BYS360_EXECUTIVE_MAIL_CENTER_V2_0_CLEAN_CORE'

def main():
    p=argparse.ArgumentParser(); p.add_argument('--project-root', default='.')
    root=Path(p.parse_args().project_root); errors=[]
    req=[
      'app/services/executive_mail_center_v2.py',
      'app/communication/executive_mail_center_v2_routes.py',
      'app/templates/executive_summary/mail_center/overview.html',
      'app/templates/executive_summary/mail_center/tasks.html',
      'app/templates/executive_summary/mail_center/recipients.html',
      'app/templates/executive_summary/mail_center/test.html',
      'app/templates/executive_summary/mail_center/logs.html',
      'app/templates/executive_summary/mail_center/scheduler.html',
      'scripts/communication/run_executive_mail_center_v2.py',
      'scripts/windows/install_bys360_executive_mail_center_v2_tasks.ps1'
    ]
    for r in req:
        if not (root/r).exists(): errors.append('eksik: '+r)
    routes=(root/'app/routes.py').read_text(encoding='utf-8', errors='ignore') if (root/'app/routes.py').exists() else ''
    if 'executive_mail_center_v2_routes' not in routes: errors.append('app/routes.py V2 route import yok')
    for r in ['app/services/executive_mail_center_v2.py','app/communication/executive_mail_center_v2_routes.py','scripts/communication/run_executive_mail_center_v2.py']:
        try: py_compile.compile(str(root/r), doraise=True)
        except Exception as exc: errors.append(f'compile hata {r}: {exc}')
    print(json.dumps({'ok': not errors, 'version': VERSION, 'errors': errors}, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(1)
    print(VERSION+'_CHECK_OK')
if __name__=='__main__': main()
