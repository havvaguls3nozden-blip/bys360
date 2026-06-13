from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PHASE5 = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL"
FIX = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_1_GATE_FIX"


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
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    if not base.exists():
        checks.append(f"Eksik dosya: {base}")
    else:
        text = read_text(base)
        for needle in [PHASE5, FIX, "corporate_information_center_v3_0_phase5.css", "Planla, denetle, güvenle gönder"]:
            if needle not in text:
                checks.append(f"{base} içinde eksik ifade: {needle}")
    py = root / ".venv" / "Scripts" / "python.exe"
    python = str(py) if py.exists() else sys.executable
    old_check = root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase5_control_panel.py"
    if old_check.exists():
        res = subprocess.run([python, str(old_check)], cwd=str(root), text=True, capture_output=True)
        if res.returncode != 0:
            checks.append((res.stdout or "") + (res.stderr or ""))
    if checks:
        print(f"{FIX}_GATE_FAIL")
        for item in checks:
            print("HATA:", item)
        return 2
    print(f"{PHASE5}_GATE_OK")
    print(f"{PHASE5}_FINAL_OK")
    print(f"{FIX}_GATE_OK")
    print(f"{FIX}_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
