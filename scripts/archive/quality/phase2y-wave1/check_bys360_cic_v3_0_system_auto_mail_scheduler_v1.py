from __future__ import annotations
import argparse
from pathlib import Path

MARKER = "BYS360_CIC_V3_0_SYSTEM_AUTO_MAIL_SCHEDULER_V1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default=r"C:\bys360\project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)
    checks = {
        root / "app/services/corporate_information_center.py": [MARKER, "def run_due_tasks", "get_auto_scheduler_config", "set_auto_scheduler_config"],
        root / "app/templates/corporate_information_center/tasks.html": ["BYS360 sistem kontrollü otomatik gönderim", "enabled_", "hour_", "minute_"],
        root / "app/templates/corporate_information_center/system.html": ["Otomatik Gönderim Zamanlayıcısı", "auto_scheduler_enabled", "auto_scheduler_late_window_minutes"],
        root / "scripts/scheduled/run_cic_auto_scheduler.py": ["run_due_tasks"],
        root / "scripts/windows/run_cic_auto_mail_scheduler.ps1": ["cic_auto_mail_scheduler.log"],
        root / "scripts/windows/install_bys360_cic_auto_mail_scheduler_task.ps1": ["BYS360 CIC Auto Mail Scheduler"],
    }
    errors = []
    for path, needles in checks.items():
        if not path.exists():
            errors.append(f"Eksik dosya: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for needle in needles:
            if needle not in text:
                errors.append(f"{path} içinde eksik ifade: {needle}")
    if errors:
        print(f"{MARKER}_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 1
    print(f"{MARKER}_GATE_OK")
    print(f"{MARKER}_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
