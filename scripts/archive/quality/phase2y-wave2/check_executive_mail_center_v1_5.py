from __future__ import annotations
import argparse, json
from pathlib import Path
VERSION='BYS360_EXECUTIVE_MAIL_CENTER_V1_5_LOCAL_CORE'
def main():
    p=argparse.ArgumentParser(); p.add_argument('--project-root', default='.')
    root=Path(p.parse_args().project_root)
    errors=[]
    required=[
        'app/services/executive_mail_center.py',
        'app/communication/executive_mail_center_routes.py',
        'app/templates/executive_summary/executive_mail_center.html',
        'scripts/communication/send_daily_pulse_check_mail.py',
        'scripts/communication/send_daily_evening_tomorrow_mail.py',
    ]
    for r in required:
        if not (root/r).exists(): errors.append(f'eksik: {r}')
    routes=(root/'app/routes.py').read_text(encoding='utf-8', errors='ignore') if (root/'app/routes.py').exists() else ''
    if 'executive_mail_center_routes' not in routes: errors.append('app/routes.py route import yok')
    comm=(root/'app/communication/daily_weather_mail_routes.py')
    if comm.exists() and 'executive_summary/executive_mail_center.html' not in comm.read_text(encoding='utf-8', errors='ignore'):
        errors.append('eski daily weather route yeni merkezi şablona yönlenmiyor')
    print(json.dumps({'ok': not errors, 'version': VERSION, 'errors': errors}, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(1)
    print(VERSION+'_CHECK_OK')
if __name__=='__main__': main()
