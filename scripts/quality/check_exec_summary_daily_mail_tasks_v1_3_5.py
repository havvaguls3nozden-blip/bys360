from __future__ import annotations
import argparse, json
from pathlib import Path
VERSION='BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3_5_PREMIUM_PEOPLE'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root', default=r'C:\bys360\project'); args=ap.parse_args(); root=Path(args.project_root)
    errors=[]
    tpl=root/'app/templates/executive_summary/daily_mail_tasks_premium.html'
    comm=root/'app/templates/communication/daily_weather_mail_settings.html'
    route=root/'app/communication/daily_weather_mail_routes.py'
    for p in [tpl,comm,route]:
        if not p.exists(): errors.append(f'eksik: {p.relative_to(root)}')
    if tpl.exists():
        txt=tpl.read_text(encoding='utf-8', errors='ignore')
        for token in ['Günlük Bilgilendirme ve Pilot Mail Yönetimi','Mail Gönderilecek Kişiler','recipient_user_ids','Çoklu Otomatik Mail Görevleri']:
            if token not in txt: errors.append(f'template token eksik: {token}')
    if route.exists():
        r=route.read_text(encoding='utf-8', errors='ignore')
        if 'executive_summary/daily_mail_tasks_premium.html' not in r: errors.append('aktif route premium template render etmiyor')
        if '/executive-summary/daily-weather-mail/settings' not in r: errors.append('executive settings post route eksik')
    print(json.dumps({'ok':not errors,'version':VERSION,'errors':errors}, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(1)
    print('BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3_5_PREMIUM_PEOPLE_CHECK_OK')
if __name__=='__main__': main()
