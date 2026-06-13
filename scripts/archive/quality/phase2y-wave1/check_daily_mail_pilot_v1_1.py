from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    errors = []
    for rel in [
        "scripts/communication/seed_daily_mail_pilot_recipients_v1_1.py",
        "scripts/communication/send_daily_pulse_check_mail.py",
        "scripts/communication/send_daily_weather_personnel_mail.py",
        "scripts/windows/install_bys360_daily_pulse_mail_task.ps1",
    ]:
        if not (root / rel).exists():
            errors.append(f"Eksik dosya: {rel}")
    try:
        import py_compile
        py_compile.compile(str(root / "scripts/communication/send_daily_pulse_check_mail.py"), doraise=True)
        py_compile.compile(str(root / "scripts/communication/seed_daily_mail_pilot_recipients_v1_1.py"), doraise=True)
    except Exception as exc:
        errors.append(f"Compile hatası: {exc}")
    result = {"ok": not errors, "version": "BYS360_DAILY_MAIL_PILOT_V1_1", "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        return 2
    print("BYS360_DAILY_MAIL_PILOT_V1_1_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
