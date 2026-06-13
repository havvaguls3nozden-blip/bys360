# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path

VERSION='BYS360_EXECUTIVE_SUMMARY_V1_0_10_ADMIN_ONLY_MENU_LOCK_CHECK'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root', default='.')
    args=ap.parse_args(); root=Path(args.project_root).resolve()
    errors=[]; markers={}
    for rel in ['app/services/settings/effective_menu.py','app/menu_registry.py','app/menu_registry_data_sections.py']:
        p=root/rel
        if not p.exists():
            errors.append(f'{rel} yok'); continue
        txt=p.read_text(encoding='utf-8', errors='ignore')
        markers[rel]='BYS360_EXECUTIVE_SUMMARY_V1_0_10_ADMIN_ONLY_MENU_LOCK' in txt
        try: py_compile.compile(str(p), doraise=True)
        except Exception as e: errors.append(f'{rel}: {e}')
    base=root/'app/templates/base.html'
    markers['app/templates/base.html']=base.exists() and 'BYS360_EXECUTIVE_SUMMARY_V1_0_10_BASE_GATE' in base.read_text(encoding='utf-8', errors='ignore')
    ok=not errors and markers.get('app/services/settings/effective_menu.py')
    print(json.dumps({'ok':ok,'version':VERSION,'errors':errors,'markers':markers}, ensure_ascii=False, indent=2))
    return 0 if ok else 2
if __name__=='__main__': raise SystemExit(main())
