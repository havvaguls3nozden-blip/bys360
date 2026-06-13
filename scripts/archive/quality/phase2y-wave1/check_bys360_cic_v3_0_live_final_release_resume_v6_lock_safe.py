from __future__ import annotations
import subprocess, sys
from pathlib import Path

VERSION = "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V6_LOCK_SAFE"
REQUIRED = [
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

def main() -> int:
    root = Path.cwd()
    if "-ProjectRoot" in sys.argv:
        i = sys.argv.index("-ProjectRoot")
        if i + 1 < len(sys.argv):
            root = Path(sys.argv[i + 1])
    errors = []
    for rel in REQUIRED:
        if not (root / rel).exists():
            errors.append(f"Eksik dosya: {root / rel}")
    if not errors:
        base = (root / "app/templates/corporate_information_center/base.html").read_text(encoding="utf-8", errors="replace")
        svc = (root / "app/services/corporate_information_center.py").read_text(encoding="utf-8", errors="replace")
        for needle in ["status_pill", "task_status", "user_initial", "cic_csrf", "corporate_information_center_v3_0_final_stable.css"]:
            if needle not in base:
                errors.append(f"base.html içinde eksik ifade: {needle}")
        for needle in ["def _cic_phase5_mail_health", "def _cic_phase5_readiness", "phase5", "phase6", "release_context"]:
            if needle not in svc:
                errors.append(f"service içinde eksik ifade: {needle}")
        if "\\n" in base or "\\'" in base or "url_for(\\'" in base:
            errors.append("base.html içinde kaçışlı newline/tırnak kalıntısı var")
    py = root / ".venv" / "Scripts" / "python.exe"
    python = str(py) if py.exists() else sys.executable
    res = subprocess.run([python, "-m", "py_compile", str(root / "app/services/corporate_information_center.py"), str(root / "app/communication/corporate_information_center_routes.py")], cwd=str(root), text=True, capture_output=True)
    if res.returncode != 0:
        errors.append((res.stdout or "") + (res.stderr or ""))
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 2
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
