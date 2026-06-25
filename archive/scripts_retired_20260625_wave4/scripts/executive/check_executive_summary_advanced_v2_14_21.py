# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
from pathlib import Path

def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    missing = []

    template = root / "app" / "templates" / "dashboard" / "executive_summary.html"
    if not template.exists():
        missing.append(str(template))
    else:
        text = read_text(template)
        for token in ["Yönetici Özeti", "Manuel gönderim", "Otomatik rapor alıcıları", "Mail gönderim logları", "00:01", "08:30"]:
            if token not in text:
                missing.append("template:" + token)

    cfg = root / "data" / "executive_summary" / "recipients.json"
    if not cfg.exists():
        missing.append(str(cfg))
    else:
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            if "recipients" not in data:
                missing.append("recipients.json:recipients")
        except Exception as exc:
            missing.append("recipients.json invalid: " + str(exc))

    routes_found = False
    for py in (root / "app").rglob("*.py"):
        if "BYS360_EXECUTIVE_SUMMARY_ADVANCED_V2_14_21_ROUTES_START" in read_text(py):
            routes_found = True
            break
    if not routes_found:
        missing.append("advanced routes marker v2.14.21")

    send_script = root / "scripts" / "executive" / "send_daily_executive_summary.py"
    if send_script.exists() and "BYS360_EXECUTIVE_SUMMARY_RECIPIENT_JSON_V2_14_21_START" not in read_text(send_script):
        missing.append("send script JSON recipient patch v2.14.21")

    if missing:
        print({"ok": False, "missing": missing})
        return 1
    print({"ok": True, "message": "Yönetici Özeti V2.14.21 gelişmiş ekran, alıcı yönetimi ve manuel gönderim altyapısı hazır."})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
