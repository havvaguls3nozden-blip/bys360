# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json
from pathlib import Path

PACKAGE = 'BYS360_PORTAL_EXPERIENCE_V3B_SOCIAL_EMBED_POSTS'
REQUIRED = [
    'app/services/portal_social_embed_service.py',
    'app/templates/portal/social_import_v3b.html',
    'app/static/css/bys360_portal_experience_v3b_social_posts.css',
    'scripts/portal/run_bys360_social_media_embed_scan_v3b.py',
]
MARKERS = {
    'app/portal/routes.py': ['BYS360_PORTAL_EXPERIENCE_V3B_SOCIAL_ROUTES_BEGIN', 'portal_social_import'],
    'app/templates/portal/_post_card.html': ['BYS360_PORTAL_EXPERIENCE_V3B_SOCIAL_EMBED_RENDER'],
    'app/templates/portal/feed.html': ['BYS360_PORTAL_EXPERIENCE_V3B_SOCIAL_WIDGETS'],
}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--project-root', required=True); args = p.parse_args()
    root = Path(args.project_root); findings=[]
    for rel in REQUIRED:
        if not (root/rel).exists(): findings.append({'file':rel,'issue':'missing'})
    for rel, markers in MARKERS.items():
        path=root/rel
        text=path.read_text(encoding='utf-8') if path.exists() else ''
        for m in markers:
            if m not in text: findings.append({'file':rel,'issue':'missing_marker','marker':m})
    ok=not findings
    print(json.dumps({'package':PACKAGE,'ok':ok,'finding_count':len(findings),'findings':findings},ensure_ascii=False,indent=2))
    return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
