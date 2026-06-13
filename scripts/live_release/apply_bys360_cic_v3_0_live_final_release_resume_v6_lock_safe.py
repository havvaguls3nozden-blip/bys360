from __future__ import annotations
import shutil, subprocess, sys, time
from pathlib import Path

VERSION = "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V6_LOCK_SAFE"
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
    return p.read_text(encoding="utf-8", errors="replace")

def copy_payload_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Avoid self-copy and Windows running-script lock issues.
    if src.resolve() == dst.resolve():
        return
    data = src.read_bytes()
    for attempt in range(5):
        try:
            dst.write_bytes(data)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(1)

def main() -> int:
    root = Path.cwd()
    if "-ProjectRoot" in sys.argv:
        i = sys.argv.index("-ProjectRoot")
        if i + 1 < len(sys.argv):
            root = Path(sys.argv[i + 1])
    elif len(sys.argv) > 1:
        root = Path(sys.argv[1])

    print(f"{VERSION} uygulanıyor...")
    print(f"ProjectRoot={root}")
    payload = root / "_cic_v6_payload"
    if not payload.exists():
        print(f"HATA: Payload klasörü bulunamadı: {payload}")
        return 2

    backup = root / "_overlay_backups" / (VERSION + "_" + time.strftime("%Y%m%d_%H%M%S"))
    backup.mkdir(parents=True, exist_ok=True)
    changed = []

    for rel in FILES:
        src = payload / rel
        dst = root / rel
        if not src.exists():
            print(f"HATA: payload eksik: {src}")
            return 2
        if dst.exists():
            b = backup / rel
            b.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(dst, b)
            except PermissionError:
                # Backup failure should not block emergency live repair; continue after noting.
                print(f"UYARI: Yedek alınamadı, dosya kullanımda olabilir: {dst}")
        copy_payload_file(src, dst)
        changed.append(rel)

    py = root / ".venv" / "Scripts" / "python.exe"
    python = str(py) if py.exists() else sys.executable
    res = subprocess.run(
        [python, "-m", "py_compile", str(root / "app/services/corporate_information_center.py"), str(root / "app/communication/corporate_information_center_routes.py")],
        cwd=str(root), text=True, capture_output=True
    )
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode

    errors = []
    base = read_text(root / "app/templates/corporate_information_center/base.html")
    svc = read_text(root / "app/services/corporate_information_center.py")
    for needle in ["status_pill", "task_status", "user_initial", "cic_csrf", "corporate_information_center_v3_0_final_stable.css"]:
        if needle not in base:
            errors.append(f"base.html içinde eksik ifade: {needle}")
    for needle in ["def _cic_phase5_mail_health", "def _cic_phase5_readiness", "phase5", "phase6", "release_context"]:
        if needle not in svc:
            errors.append(f"service içinde eksik ifade: {needle}")
    # Check only literal backslash-n / escaped quote residue, not real line breaks.
    if "\\n" in base or "\\'" in base or 'url_for(\\' in base:
        errors.append("base.html içinde kaçışlı newline/tırnak kalıntısı var")
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 2

    print(f"{VERSION}_APPLY_OK")
    print("Güncellenen dosyalar:")
    for rel in changed:
        print(" -", rel)
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
