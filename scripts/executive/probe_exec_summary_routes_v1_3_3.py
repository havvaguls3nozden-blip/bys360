# -*- coding: utf-8 -*-
from pathlib import Path
import re, json, sys

def main():
    root = Path(sys.argv[1]) if len(sys.argv)>1 else Path.cwd()
    patterns = ['daily-weather-mail','gunluk-hava-maili','yonetici-ozeti','executive-summary','daily_weather_mail','daily_weather_mail_tasks']
    hits=[]
    for p in list(root.glob('app/**/*.py')) + list(root.glob('app/templates/**/*.html')):
        try:
            txt=p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        if any(x in txt for x in patterns):
            lines=[]
            for i,line in enumerate(txt.splitlines(),1):
                if any(x in line for x in patterns) or 'render_template' in line or '@' in line and 'route' in line:
                    lines.append({'line':i,'text':line[:220]})
            hits.append({'file':str(p.relative_to(root)), 'lines':lines[:80]})
    out={'ok':True,'root':str(root),'hits':hits}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0
if __name__=='__main__':
    raise SystemExit(main())
