# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path

PACKAGE = 'BYS360_PORTAL_EXPERIENCE_V3A2_NEWS_HARDENING'

REQUIRED = {
    'app/services/portal_press_news_service.py': [
        'BYS360 Portal V3A2', 'DEFAULT_TRUSTED_HOSTS', '_relevance_score',
        'duplicates_merged', 'BYS360_PRESS_NEWS_SCAN_V3A2_HEALTH_REPORT.json'
    ],
    'app/templates/portal/press_news_review_v3a.html': [
        'press-news-health-grid-v3a2', 'Alaka:', 'Son Elenenler'
    ],
    'app/static/css/bys360_portal_experience_v3a_press_news.css': [
        'BYS360_PORTAL_EXPERIENCE_V3A2_NEWS_HARDENING', 'press-news-health-grid-v3a2'
    ],
    'scripts/portal/run_bys360_press_news_scan_v3a.py': ['scan_press_news_candidates'],
    'app/portal/routes.py': ['portal_press_news_review', 'portal_press_news_scan_now', 'portal_press_news_publish'],
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    findings = []
    for rel, needles in REQUIRED.items():
        path = root / rel
        if not path.exists():
            findings.append({'file': rel, 'issue': 'missing'})
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        for needle in needles:
            if needle not in text:
                findings.append({'file': rel, 'issue': f'missing marker: {needle}'})
    for rel in ['app/services/portal_press_news_service.py', 'scripts/portal/run_bys360_press_news_scan_v3a.py']:
        try:
            py_compile.compile(str(root / rel), doraise=True)
        except Exception as exc:
            findings.append({'file': rel, 'issue': str(exc)})
    result = {'package': PACKAGE, 'ok': not findings, 'finding_count': len(findings), 'findings': findings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
