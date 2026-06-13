from __future__ import annotations
import argparse, json
from pathlib import Path
VERSION="BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3_1_ROUTE_FIX"
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root', default=r'C:\bys360\project'); args=ap.parse_args(); root=Path(args.project_root)
    errors=[]
    tpl=root/'app/templates/executive_summary/daily_weather_mail_tasks.html'
    if not tpl.exists(): errors.append('template bulunamadi')
    found=False
    for p in (root/'app').rglob('*.py'):
        try: txt=p.read_text(encoding='utf-8', errors='ignore')
        except Exception: continue
        if 'daily_weather_mail_tasks.html' in txt and 'daily-weather-mail' in txt:
            found=True; break
    if not found: errors.append('route patch bulunamadi')
    res={'ok': not errors, 'version': VERSION, 'errors': errors}
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(1)
    print('BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3_1_ROUTE_FIX_CHECK_OK')
if __name__=='__main__': main()
