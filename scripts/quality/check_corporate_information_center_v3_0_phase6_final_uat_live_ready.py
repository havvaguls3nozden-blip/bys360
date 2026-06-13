from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY"


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--project-root", "-ProjectRoot", dest="project_root", default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.project_root).resolve() if args.project_root else Path(__file__).resolve().parents[2]
    checks: list[str] = []
    required = {
        root / "app/services/corporate_information_center.py": [VERSION, "def _cic_phase6_build", "phase6_uat_score", "_cic_phase6_previous_context"],
        root / "app/templates/corporate_information_center/base.html": [VERSION, "corporate_information_center_v3_0_phase6.css", "Final UAT"],
        root / "app/templates/corporate_information_center/overview.html": [VERSION, "Final UAT ve Canlı Hazırlık Paneli", "phase6.uat_score"],
        root / "app/templates/corporate_information_center/tasks.html": [VERSION, "Görev Çalıştırma Güvenlik Kapısı", "phase6.top_checks"],
        root / "app/templates/corporate_information_center/recipients.html": [VERSION, "Alıcı Veri Kalitesi", "phase6.recipient_quality"],
        root / "app/templates/corporate_information_center/templates.html": [VERSION, "Şablon Canlı Yayın Kontrolü", "phase6.template_quality"],
        root / "app/templates/corporate_information_center/test.html": [VERSION, "Gerçek Gönderim Son Kontrol Kapısı", "phase6.final_send_checks"],
        root / "app/templates/corporate_information_center/logs.html": [VERSION, "Denetim ve İzlenebilirlik Özeti", "phase6.log_quality"],
        root / "app/templates/corporate_information_center/system.html": [VERSION, "Final UAT Senaryo Kapısı", "phase6.scenarios"],
        root / "app/static/css/corporate_information_center_v3_0_phase6.css": [VERSION, "cic-phase6-scenarios", "cic-phase6-live-gate"],
        root / "docs/BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_UAT_LIVE_READY_REPORT.md": [VERSION, "UAT senaryoları"],
    }
    for path, needles in required.items():
        if not path.exists():
            checks.append(f"Eksik dosya: {path}")
            continue
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                checks.append(f"{path} içinde eksik ifade: {needle}")
    for name in ["tasks.html", "recipients.html", "templates.html", "test.html", "system.html"]:
        p = root / "app/templates/corporate_information_center" / name
        if p.exists():
            t = read_text(p)
            if 'method="post"' in t.lower() and "cic_csrf()" not in t and "csrf_token" not in t:
                checks.append(f"{p} içinde CSRF token görünmüyor")
    py = root / ".venv" / "Scripts" / "python.exe"
    python = str(py) if py.exists() else sys.executable
    files = [root / "app" / "services" / "corporate_information_center.py", root / "app" / "communication" / "corporate_information_center_routes.py"]
    res = subprocess.run([python, "-m", "py_compile", *map(str, [f for f in files if f.exists()])], cwd=str(root), text=True, capture_output=True)
    if res.returncode != 0:
        checks.append((res.stdout or "") + (res.stderr or ""))
    if checks:
        print(f"{VERSION}_GATE_FAIL")
        for item in checks:
            print("HATA:", item)
        return 2
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
