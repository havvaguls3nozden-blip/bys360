from __future__ import annotations
import json, re
from pathlib import Path
VERSION="BYS360_DAILY_MAIL_TASKS_V1_4_STABLE_AUTOMATION_UI"

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--project-root', default='.')
    args=p.parse_args(); root=Path(args.project_root)
    errors=[]
    route=root/'app/communication/daily_weather_mail_routes.py'
    if not route.exists(): errors.append('daily_weather_mail_routes.py yok')
    else:
        text=route.read_text(encoding='utf-8', errors='replace')
        if 'executive_summary/daily_mail_tasks_v1_4.html' not in text: errors.append('aktif route V1.4 template render etmiyor')
    for rel in ['app/templates/executive_summary/daily_mail_tasks_v1_4.html','scripts/communication/send_daily_pulse_check_mail.py','scripts/windows/install_bys360_daily_mail_tasks_v1_4.ps1']:
        if not (root/rel).exists(): errors.append(f'{rel} yok')
    inst=root/'scripts/windows/install_bys360_daily_mail_tasks_v1_4.ps1'
    if inst.exists():
        s=inst.read_text(encoding='utf-8', errors='replace')
        if '& "$Python" "$Runner"' not in s: errors.append('launcher PowerShell & ile python calistirmiyor')
        if 'BYS360 Daily Pulse Check Mail' not in s: errors.append('gun ortasi gorevi installer icinde yok')
    print(json.dumps({'ok': not errors, 'version': VERSION, 'errors': errors}, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(2)
    print('BYS360_DAILY_MAIL_TASKS_V1_4_STABLE_AUTOMATION_UI_CHECK_OK')
if __name__=='__main__': main()
