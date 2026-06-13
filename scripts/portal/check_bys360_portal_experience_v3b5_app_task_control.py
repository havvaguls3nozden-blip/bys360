# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json
from pathlib import Path
PACKAGE='BYS360_PORTAL_EXPERIENCE_V3B5_APP_TASK_CONTROL'
REQUIRED=[
 'app/templates/portal/social_import_v3b.html',
 'app/static/css/bys360_portal_experience_v3b5_task_control.css',
 'app/services/portal_social_task_service.py',
 'app/services/portal_social_embed_service.py',
 'app/portal/routes.py',
]
def read(p):
 try: return p.read_text(encoding='utf-8')
 except Exception: return ''
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--project-root', required=True); args=ap.parse_args(); root=Path(args.project_root); findings=[]
 for rel in REQUIRED:
  if not (root/rel).exists(): findings.append({'level':'error','file':rel,'message':'Dosya bulunamadı'})
 tmpl=read(root/'app/templates/portal/social_import_v3b.html')
 for needle in ['Otomatik Kontrolü Aç','Şimdi Çalıştır','Otomatik Kontrolü Kapat','social-v3b5-task-panel']:
  if needle not in tmpl: findings.append({'level':'error','file':'app/templates/portal/social_import_v3b.html','message':needle+' bulunamadı'})
 routes=read(root/'app/portal/routes.py')
 for needle in ['portal_social_import_task_install','portal_social_import_task_remove','portal_social_import_task_run_now']:
  if needle not in routes: findings.append({'level':'error','file':'app/portal/routes.py','message':needle+' route bulunamadı'})
 svc=read(root/'app/services/portal_social_task_service.py')
 for needle in ['install_social_auto_task','remove_social_auto_task','run_social_auto_import_now','get_social_auto_task_status']:
  if needle not in svc: findings.append({'level':'error','file':'app/services/portal_social_task_service.py','message':needle+' bulunamadı'})
 ok=not any(f['level']=='error' for f in findings); print(json.dumps({'package':PACKAGE,'ok':ok,'finding_count':len(findings),'findings':findings},ensure_ascii=False,indent=2)); return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
