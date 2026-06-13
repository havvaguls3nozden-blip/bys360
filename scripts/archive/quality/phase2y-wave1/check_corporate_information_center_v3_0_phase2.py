from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path
VERSION="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE2"

def main():
    p=argparse.ArgumentParser(); p.add_argument('--project-root', default='.')
    root=Path(p.parse_args().project_root)
    errors=[]
    required=[
      'app/services/corporate_information_center_engine.py',
      'scripts/communication/run_corporate_information_center_task_v3_0_phase2.py',
      'scripts/windows/install_corporate_information_center_tasks_v3_0_phase2.ps1',
    ]
    for r in required:
        if not (root/r).exists(): errors.append(f'eksik: {r}')
    for r in required[:2]:
        try: py_compile.compile(str(root/r), doraise=True)
        except Exception as e: errors.append(f'compile hata {r}: {e}')
    svc=(root/'app/services/corporate_information_center_engine.py').read_text(encoding='utf-8', errors='ignore') if (root/'app/services/corporate_information_center_engine.py').exists() else ''
    for key in ['PERSONEL_MORNING','PERSONEL_NOON','PERSONEL_EVENING','MANAGER_MORNING','MANAGER_EVENING','run_task','dashboard_context']:
        if key not in svc: errors.append(f'engine içinde yok: {key}')
    print(json.dumps({'ok': not errors, 'version': VERSION, 'errors': errors}, ensure_ascii=False, indent=2))
    if errors: raise SystemExit(1)
    print(VERSION+'_CHECK_OK')
if __name__=='__main__': main()
