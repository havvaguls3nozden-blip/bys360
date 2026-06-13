# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from pathlib import Path
MARKER = "BYS360_CIC_V3_0_RECIPIENTS_SAVE_PERSISTENCE_V2"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-ProjectRoot", default="C:\\bys360\\project")
    args = ap.parse_args()
    root = Path(args.ProjectRoot)
    checks = [
        (root / "app/templates/corporate_information_center/recipients.html", [MARKER, "corporate_information_center_recipients_save", "staff_user_ids", "manager_user_ids", "debug_staff_count"]),
        (root / "app/static/css/corporate_information_center_recipients_save_v2.css", [MARKER, "cic-rec2"]),
        (root / "app/static/js/corporate_information_center_recipients_save_v2.js", [MARKER, "data-rec2-mirror", "staff_user_ids", "manager_user_ids"]),
        (root / "app/services/corporate_information_center.py", [MARKER, "last_recipient_save_summary", "def save_recipients"]),
    ]
    errors = []
    for path, needles in checks:
        if not path.exists():
            errors.append(f"Eksik dosya: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for n in needles:
            if n not in text:
                errors.append(f"{path} içinde eksik ifade: {n}")
        if "\\n" in text[:500]:
            errors.append(f"{path} içinde kaçışlı newline kalıntısı var")
    if errors:
        print("BYS360_CIC_V3_0_RECIPIENTS_SAVE_PERSISTENCE_V2_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 1
    print("BYS360_CIC_V3_0_RECIPIENTS_SAVE_PERSISTENCE_V2_GATE_OK")
    print("BYS360_CIC_V3_0_RECIPIENTS_SAVE_PERSISTENCE_V2_FINAL_OK")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
