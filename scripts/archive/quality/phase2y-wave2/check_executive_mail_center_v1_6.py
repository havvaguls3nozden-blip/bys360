from __future__ import annotations
import argparse, json
from pathlib import Path
VERSION="BYS360_EXECUTIVE_MAIL_CENTER_V1_6_FULL_PAGES"
def main():
    p=argparse.ArgumentParser(); p.add_argument('--project-root', default='.')
    root=Path(p.parse_args().project_root)
    errors=[]
    required=[
        'app/services/executive_mail_center.py',
        'app/communication/executive_mail_center_routes.py',
        'app/templates/executive_summary/executive_mail_center.html',
        'app/templates/executive_summary/executive_mail_tasks.html',
        'app/templates/executive_summary/executive_mail_recipients.html',
        'app/templates/executive_summary/executive_mail_logs.html',
        'app/templates/executive_summary/executive_mail_test.html',
        'app/templates/executive_summary/executive_mail_scheduled_jobs.html',
        'scripts/windows/install_bys360_daily_mail_tasks_v1_6.ps1',
    ]
    for r in required:
        if not (root/r).exists(): errors.append(f'eksik: {r}')
    routes=(root/'app/routes.py').read_text(encoding='utf-8', errors='ignore') if (root/'app/routes.py').exists() else ''
    if 'executive_mail_center_routes' not in routes:
        errors.append('app/routes.py executive_mail_center_routes import yok')
    center_route=(root/'app/communication/executive_mail_center_routes.py').read_text(encoding='utf-8', errors='ignore') if (root/'app/communication/executive_mail_center_routes.py').exists() else ''
    for marker in ['/executive-summary/mail-center/tasks','/executive-summary/mail-center/recipients','/executive-summary/mail-center/logs','/executive-summary/mail-center/test-send','/executive-summary/mail-center/scheduled-jobs']:
        if marker not in center_route:
            errors.append(f'route eksik: {marker}')
    comm=root/'app/communication/daily_weather_mail_routes.py'
    if comm.exists() and 'executive_summary/executive_mail_center.html' not in comm.read_text(encoding='utf-8', errors='ignore'):
        errors.append('eski günlük hava route ana merkeze yönlenmiyor')
    print(json.dumps({'ok': not errors, 'version': VERSION, 'errors': errors}, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(1)
    print(VERSION+'_CHECK_OK')
if __name__=='__main__': main()
