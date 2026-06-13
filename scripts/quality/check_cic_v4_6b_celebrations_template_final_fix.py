from __future__ import annotations
import argparse
from pathlib import Path

CSS_NAME = 'corporate_information_center_v4_6b_celebrations_final.css'
JS_NAME = 'corporate_information_center_v4_6b_celebrations_final.js'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project-root', default='.')
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    tpl = root / 'app/templates/corporate_information_center/celebrations.html'
    base = root / 'app/templates/corporate_information_center/base.html'
    css = root / 'app/static/css' / CSS_NAME
    js = root / 'app/static/js' / JS_NAME
    errors = []
    for p in (tpl, base, css, js):
        if not p.exists(): errors.append(f'missing: {p}')
    text = tpl.read_text(encoding='utf-8') if tpl.exists() else ''
    base_text = base.read_text(encoding='utf-8') if base.exists() else ''
    if '[:8]' in text: errors.append('python-style slice remains in celebrations template')
    if CSS_NAME not in base_text: errors.append('v4.6b css ref missing from corporate information base')
    if JS_NAME not in base_text: errors.append('v4.6b js ref missing from corporate information base')
    if '{% block title %}' in base_text and '<link' in base_text.split('{% block title %}',1)[-1].split('{% endblock %}',1)[0]:
        errors.append('css link still appears inside title block')
    try:
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader(str(root / 'app/templates')))
        env.get_template('corporate_information_center/celebrations.html')
        env.get_template('corporate_information_center/base.html')
    except Exception as exc:
        errors.append(f'jinja parse failed: {exc!r}')
    if errors:
        print('BYS360_CIC_V4_6B_CELEBRATIONS_TEMPLATE_FINAL_FIX_CHECK_FAIL')
        for e in errors: print('ERROR=', e)
        return 1
    print('BYS360_CIC_V4_6B_CELEBRATIONS_TEMPLATE_FINAL_FIX_CHECK_OK')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
