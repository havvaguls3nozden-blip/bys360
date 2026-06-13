# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json
from pathlib import Path
PACKAGE='BYS360_PORTAL_EXPERIENCE_V3B3_SOCIAL_IMPORT_CENTER'
REQUIRED=[
 'app/templates/portal/social_import_v3b.html',
 'app/static/css/bys360_portal_experience_v3b3_social_import_center.css',
]
MARKERS=[
 ('app/templates/portal/social_import_v3b.html','social-v3b3-shell'),
 ('app/templates/portal/social_import_v3b.html','Hesapları Kontrol Et ve Paylaş'),
 ('app/templates/portal/social_import_v3b.html','Yayın Akışına Ekle'),
 ('app/static/css/bys360_portal_experience_v3b3_social_import_center.css','social-v3b3-hero'),
]
def main():
 p=argparse.ArgumentParser(); p.add_argument('--project-root',required=True); args=p.parse_args(); root=Path(args.project_root)
 findings=[]
 for rel in REQUIRED:
  if not (root/rel).exists(): findings.append({'type':'missing_file','file':rel})
 for rel,marker in MARKERS:
  path=root/rel
  if path.exists() and marker not in path.read_text(encoding='utf-8',errors='ignore'):
   findings.append({'type':'missing_marker','file':rel,'marker':marker})
 result={'package':PACKAGE,'ok':not findings,'finding_count':len(findings),'findings':findings}
 print(json.dumps(result,ensure_ascii=False,indent=2))
 return 0 if result['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
