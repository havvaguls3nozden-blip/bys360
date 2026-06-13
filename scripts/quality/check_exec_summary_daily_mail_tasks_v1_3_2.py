from pathlib import Path
import sys,json
root=Path(sys.argv[sys.argv.index('--project-root')+1]) if '--project-root' in sys.argv else Path.cwd()
errors=[]
t=root/'app/templates/executive_summary/daily_weather_mail_tasks.html'
if not t.exists(): errors.append('template yok')
elif 'Çoklu Günlük Mail Görevleri' not in t.read_text(encoding='utf-8',errors='ignore'): errors.append('template yeni icerik degil')
route_ok=False
for f in [root/'app/dashboard/executive_summary_routes.py',root/'app/dashboard/routes.py',root/'app/executive_summary/routes.py',root/'app/routes.py']:
    if f.exists():
        txt=f.read_text(encoding='utf-8',errors='ignore')
        if 'daily_weather_mail_tasks.html' in txt and 'daily-weather-mail' in txt:
            route_ok=True
if not route_ok: errors.append('route yeni templatee bagli degil')
print(json.dumps({'ok':not errors,'version':'BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3_2_FORCE_TEMPLATE','errors':errors},ensure_ascii=False,indent=2))
if errors: sys.exit(1)
print('BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3_2_FORCE_TEMPLATE_CHECK_OK')
