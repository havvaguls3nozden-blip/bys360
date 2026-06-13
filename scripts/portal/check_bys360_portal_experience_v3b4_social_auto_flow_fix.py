# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json
from pathlib import Path
PACKAGE='BYS360_PORTAL_EXPERIENCE_V3B4_SOCIAL_AUTO_FLOW_FIX'
REQUIRED=[
 'app/templates/portal/social_import_v3b.html',
 'app/static/css/bys360_portal_experience_v3b4_social_auto_flow.css',
 'app/services/portal_social_embed_service.py',
 'app/portal/routes.py',
 'app/templates/base.html',
 'app/templates/portal/_tabs.html',
]
def read(p):
 try: return p.read_text(encoding='utf-8')
 except Exception: return ''
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--project-root', required=True); args=ap.parse_args(); root=Path(args.project_root)
 findings=[]
 for rel in REQUIRED:
  if not (root/rel).exists(): findings.append({'level':'error','file':rel,'message':'Dosya bulunamadı'})
 tmpl=read(root/'app/templates/portal/social_import_v3b.html')
 for needle in ['Önce Tara','Bulunanları Paylaş','Günlük otomatik kontrol','social-v3b4-shell']:
  if needle not in tmpl: findings.append({'level':'error','file':'app/templates/portal/social_import_v3b.html','message':needle+' bulunamadı'})
 svc=read(root/'app/services/portal_social_embed_service.py')
 for needle in ['discover_and_queue_social_links','source: str =','BYS360_SOCIAL_MEDIA_AUTO_IMPORT_V3B4_LAST_REPORT.json']:
  if needle not in svc: findings.append({'level':'error','file':'app/services/portal_social_embed_service.py','message':needle+' bulunamadı'})
 base=read(root/'app/templates/base.html')
 sidebar_count=base.count('main.portal_social_import') + base.count("'/portal/social-import'")
 # base içinde fallback de sayıldığı için tam sayım yapmıyoruz; görünür nav satır sayısı kontrolü
 nav_count=base.count('Sosyal Medya Gönderisi Ekle')
 if nav_count != 1: findings.append({'level':'error','file':'app/templates/base.html','message':f'Sol şerit sosyal medya sekmesi sayısı {nav_count}; 1 olmalı'})
 tabs=read(root/'app/templates/portal/_tabs.html')
 tab_count=tabs.count('Sosyal Medya Gönderisi')
 if tab_count != 1: findings.append({'level':'error','file':'app/templates/portal/_tabs.html','message':f'Portal üst sekme sayısı {tab_count}; 1 olmalı'})
 ok=not any(f.get('level')=='error' for f in findings)
 print(json.dumps({'package':PACKAGE,'ok':ok,'finding_count':len(findings),'findings':findings}, ensure_ascii=False, indent=2))
 return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
