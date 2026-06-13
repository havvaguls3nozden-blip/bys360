from __future__ import annotations
import argparse
import py_compile
from pathlib import Path

MARKER = "BYS360_CIC_V3_0_AUTO_MAIL_WEEKDAY_ONLY_V1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default=r"C:\bys360\project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)
    checks = {
        root / "app/services/corporate_information_center.py": [MARKER, "weekdays_only", "weekend_blocked", "Hafta sonu otomatik gönderim kapalı", "def run_due_tasks"],
        root / "app/templates/corporate_information_center/system.html": ["auto_scheduler_weekdays_only", "Sadece hafta içi gönder", "Hafta sonu koruması"],
        root / "app/templates/corporate_information_center/tasks.html": ["Hafta sonu gönderim yapılmaz"],
        root / "scripts/scheduled/run_cic_auto_scheduler.py": ["BYS360_CIC_WEEKEND_MAIL_BLOCKED_OK", "run_due_tasks"],
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
    try:
        py_compile.compile(str(root / "app/services/corporate_information_center.py"), doraise=True)
        py_compile.compile(str(root / "scripts/scheduled/run_cic_auto_scheduler.py"), doraise=True)
    except Exception as exc:
        errors.append(f"Python derleme hatası: {exc}")
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
