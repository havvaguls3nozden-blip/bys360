from __future__ import annotations

import subprocess
import sys
from pathlib import Path

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL"


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    checks: list[str] = []
    required = {
        root / "app/services/corporate_information_center.py": [VERSION, "def _cic_phase5_mail_health", "def _cic_phase5_readiness", "phase5.audit", "def context("],
        root / "app/templates/corporate_information_center/base.html": [VERSION, "corporate_information_center_v3_0_phase5.css", "Planla, denetle, güvenle gönder"],
        root / "app/templates/corporate_information_center/overview.html": [VERSION, "Yönetici Kontrol Paneli", "Görev Bazlı Gönderim Ön İzleme"],
        root / "app/templates/corporate_information_center/tasks.html": [VERSION, "Görev Yönetimi ve Çalıştırma Kontrolü", "data-confirm-real"],
        root / "app/templates/corporate_information_center/recipients.html": [VERSION, "Canlı Alıcı Özeti", "missingMailCount"],
        root / "app/templates/corporate_information_center/templates.html": [VERSION, "İçerik Kontrolü", "data-template-quality"],
        root / "app/templates/corporate_information_center/test.html": [VERSION, "Test ve Gönderim Merkezi", "realSendWarning"],
        root / "app/templates/corporate_information_center/logs.html": [VERSION, "Gönderim Geçmişi", "logType"],
        root / "app/templates/corporate_information_center/system.html": [VERSION, "Sistem Sağlığı ve Denetim", "Denetim İzi"],
        root / "app/static/css/corporate_information_center_v3_0_phase5.css": [VERSION, "cic-readiness-ring", "cic-phase5-checklist"],
    }
    for path, needles in required.items():
        if not path.exists():
            checks.append(f"Eksik dosya: {path}")
            continue
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                checks.append(f"{path} içinde eksik ifade: {needle}")
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
