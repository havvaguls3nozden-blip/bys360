from __future__ import annotations
import argparse, json
from pathlib import Path
VERSION='BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root', default=r'C:\bys360\project'); args=ap.parse_args()
    root=Path(args.project_root); errors=[]
    required=[
      'app/templates/executive_summary/daily_weather_mail_tasks.html',
      'scripts/executive/repair_executive_summary_daily_mail_tasks_v1_3.py',
      'scripts/windows/repair_executive_summary_daily_mail_tasks_v1_3.ps1',
      'scripts/windows/install_bys360_daily_pulse_mail_task.ps1'
    ]
    for rel in required:
        if not (root/rel).exists(): errors.append(f'eksik dosya: {rel}')
    route_ok=False
    for p in (root/'app').rglob('*.py'):
        try:
            if 'BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3' in p.read_text(encoding='utf-8', errors='ignore'):
                route_ok=True; break
        except Exception: pass
    if not route_ok: errors.append('route patch bulunamadi')
    print(json.dumps({'ok': not errors, 'version': VERSION, 'errors': errors}, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(1)
    print('BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3_CHECK_OK')
if __name__=='__main__': main()
