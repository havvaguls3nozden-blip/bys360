from __future__ import annotations
import shutil, subprocess, sys
from pathlib import Path
VERSION = "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V5_DIRECT_STABLE"
FILES = [
"app/services/corporate_information_center.py",
"app/communication/corporate_information_center_routes.py",
"app/templates/corporate_information_center/base.html",
"app/templates/corporate_information_center/overview.html",
"app/templates/corporate_information_center/tasks.html",
"app/templates/corporate_information_center/recipients.html",
"app/templates/corporate_information_center/templates.html",
"app/templates/corporate_information_center/test.html",
"app/templates/corporate_information_center/logs.html",
"app/templates/corporate_information_center/system.html",
"app/static/css/corporate_information_center_v3_0_final_stable.css",
]

def read_text(p: Path) -> str:
    return p.read_text(encoding='utf-8', errors='replace')

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    print(f"{VERSION} uygulanıyor...")
    print(f"ProjectRoot={root}")
    backup = root / '_overlay_backups' / VERSION
    backup.mkdir(parents=True, exist_ok=True)
    overlay_root = Path(__file__).resolve().parents[2]
    changed=[]
    for rel in FILES:
        src = overlay_root / rel
        dst = root / rel
        if not src.exists():
            print(f"HATA: payload eksik: {src}")
            return 2
        if dst.exists():
            b = backup / rel
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, b)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        changed.append(rel)
    py = root / '.venv' / 'Scripts' / 'python.exe'
    python = str(py) if py.exists() else sys.executable
    res = subprocess.run([python, '-m', 'py_compile', str(root/'app/services/corporate_information_center.py'), str(root/'app/communication/corporate_information_center_routes.py')], cwd=str(root), text=True, capture_output=True)
    if res.returncode != 0:
        print(res.stdout); print(res.stderr)
        return res.returncode
    errors=[]
    base = read_text(root/'app/templates/corporate_information_center/base.html')
    for needle in ['status_pill', 'task_status', 'user_initial', 'cic_csrf', 'BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V5_DIRECT_STABLE']:
        if needle not in base and needle != 'BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V5_DIRECT_STABLE':
            errors.append(f'base.html içinde eksik ifade: {needle}')
    svc = read_text(root/'app/services/corporate_information_center.py')
    for needle in ['def _cic_phase5_mail_health', 'def _cic_phase5_readiness', 'phase5', 'phase6', 'release_context']:
        if needle not in svc:
            errors.append(f'service içinde eksik ifade: {needle}')
    if '\n' in base or "\'" in base:
        errors.append('base.html içinde kaçışlı newline/tırnak kalıntısı var')
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for e in errors: print('HATA:', e)
        return 2
    print(f"{VERSION}_APPLY_OK")
    print('Güncellenen dosyalar:')
    for rel in changed: print(' -', rel)
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
