from __future__ import annotations
import sys, shutil, re, json
from pathlib import Path
from datetime import datetime
VERSION='BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3_2_FORCE_TEMPLATE'

def main():
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd()
    src=root/'app/templates/executive_summary/daily_weather_mail_tasks.html'
    route_candidates=[
        root/'app/dashboard/executive_summary_routes.py',
        root/'app/dashboard/routes.py',
        root/'app/executive_summary/routes.py',
        root/'app/routes.py',
    ]
    out={'ok':False,'version':VERSION,'template_exists':src.exists(),'patched_files':[],'errors':[]}
    backup=root/'backups'/f'{VERSION}_{datetime.now():%Y%m%d_%H%M%S}'
    backup.mkdir(parents=True,exist_ok=True)
    # Ensure template contains V3 text
    if not src.exists() or 'Çoklu Günlük Mail Görevleri' not in src.read_text(encoding='utf-8',errors='ignore'):
        out['errors'].append('Yeni template bulunamadi veya icerik eski')
    route_file=None
    for f in route_candidates:
        if f.exists():
            txt=f.read_text(encoding='utf-8',errors='ignore')
            if 'daily-weather-mail' in txt or 'gunluk-hava-maili' in txt or 'daily_weather_mail' in txt:
                route_file=f; break
    if not route_file:
        for f in route_candidates:
            if f.exists(): route_file=f; break
    if not route_file:
        out['errors'].append('Route dosyasi bulunamadi')
        print(json.dumps(out,ensure_ascii=False,indent=2)); return 1
    txt=route_file.read_text(encoding='utf-8',errors='ignore')
    shutil.copy2(route_file, backup/route_file.name)
    # Add import render_template if missing
    if 'render_template' not in txt:
        txt=txt.replace('from flask import ', 'from flask import render_template, ', 1) if 'from flask import ' in txt else 'from flask import render_template\n'+txt
    # Find daily-weather route function block and force return template
    lines=txt.splitlines()
    new=[]; i=0; patched=False
    while i<len(lines):
        line=lines[i]
        if ('daily-weather-mail' in line or 'gunluk-hava-maili' in line) and line.lstrip().startswith('@'):
            # copy decorators until function
            while i<len(lines):
                new.append(lines[i]); i+=1
                if i<len(lines) and lines[i].lstrip().startswith('def '):
                    fn=lines[i]; new.append(fn); i+=1
                    indent=re.match(r'(\s*)', fn).group(1)+'    '
                    new.append(indent+"return render_template('executive_summary/daily_weather_mail_tasks.html')")
                    # skip old function body until next decorator/function at same or lower indent
                    while i<len(lines):
                        nxt=lines[i]
                        if nxt.startswith('@') or (nxt and not nxt.startswith((' ', '\t')) and (nxt.startswith('def ') or nxt.startswith('class '))):
                            break
                        i+=1
                    patched=True
                    break
            continue
        new.append(line); i+=1
    txt2='\n'.join(new)+'\n'
    # If no route found, append fallback to first blueprint/app-like route decorator variable by using dashboard_bp likely
    if not patched:
        bp='dashboard_bp'
        m=re.search(r'(\w+)_bp\s*=\s*Blueprint|Blueprint\([\'\"]([^\'\"]+)', txt2)
        if 'executive_summary_bp' in txt2: bp='executive_summary_bp'
        elif 'dashboard_bp' in txt2: bp='dashboard_bp'
        elif 'bp = Blueprint' in txt2: bp='bp'
        txt2 += f"\n# {VERSION}\n@{bp}.route('/executive-summary/daily-weather-mail')\n@{bp}.route('/yonetici-ozeti/gunluk-hava-maili')\ndef executive_summary_daily_weather_mail_tasks_v132():\n    return render_template('executive_summary/daily_weather_mail_tasks.html')\n"
        patched=True
    route_file.write_text(txt2,encoding='utf-8')
    out['patched_files'].append(str(route_file.relative_to(root)))
    out['ok']=not out['errors'] and patched
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
