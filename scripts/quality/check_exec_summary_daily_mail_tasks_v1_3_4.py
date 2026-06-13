from __future__ import annotations
import argparse, json
from pathlib import Path

VERSION = "BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3_4_ROUTE_PRIORITY_FIX"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    errors = []
    route_file = root / "app" / "communication" / "daily_weather_mail_routes.py"
    template = root / "app" / "templates" / "executive_summary" / "daily_weather_mail_tasks.html"
    if not route_file.exists():
        errors.append("communication route dosyası yok")
        text = ""
    else:
        text = route_file.read_text(encoding="utf-8", errors="replace")
    if not template.exists():
        errors.append("çoklu görev şablonu yok")
    if "executive_summary/daily_weather_mail_tasks.html" not in text:
        errors.append("communication route hâlâ yeni şablonu render etmiyor")
    if "communication/daily_weather_mail_settings.html" in text:
        errors.append("communication route içinde eski şablon referansı hâlâ var")
    result = {"ok": not errors, "version": VERSION, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        return 1
    print("BYS360_EXECUTIVE_SUMMARY_DAILY_MAIL_TASKS_V1_3_4_ROUTE_PRIORITY_FIX_CHECK_OK")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
