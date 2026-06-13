# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path

PACKAGE='BYS360_PORTAL_EXPERIENCE_V3B2_SOCIAL_AUTO_IMPORT'
REQUIRED={
 'app/services/portal_social_embed_service.py':['discover_latest_social_links','watch_sources','auto_discover'],
 'app/templates/portal/social_import_v3b.html':['Kurumsal hesapları kontrol et','Hesapları Kontrol Et ve Paylaş','Yayın Akışına Ekle'],
 'app/static/css/bys360_portal_experience_v3b2_social_auto_import.css':['social-auto-v3b2-shell'],
 'scripts/portal/run_bys360_social_media_embed_scan_v3b.py':['--auto-discover'],
 'app/portal/routes.py':['portal_social_import_auto_scan'],
}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--project-root',required=True); args=parser.parse_args()
    root=Path(args.project_root); findings=[]
    for rel,markers in REQUIRED.items():
        p=root/rel
        if not p.exists(): findings.append({'file':rel,'issue':'missing'}); continue
        text=p.read_text(encoding='utf-8')
        for m in markers:
            if m not in text: findings.append({'file':rel,'issue':'marker_missing','marker':m})
    for rel in ['app/services/portal_social_embed_service.py','scripts/portal/run_bys360_social_media_embed_scan_v3b.py','scripts/portal/check_bys360_portal_experience_v3b2_social_auto_import.py']:
        p=root/rel
        if p.exists():
            try: py_compile.compile(str(p), doraise=True)
            except Exception as exc: findings.append({'file':rel,'issue':'compile_error','error':str(exc)})
    print(json.dumps({'package':PACKAGE,'ok':not findings,'finding_count':len(findings),'findings':findings},ensure_ascii=False,indent=2))
    return 0 if not findings else 1
if __name__=='__main__': raise SystemExit(main())
