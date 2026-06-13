# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from pathlib import Path

MARKER = "BYS360_CIC_V3_0_RECIPIENTS_PRO_USABILITY_V1"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-ProjectRoot", default="C:\\bys360\\project")
    args = ap.parse_args()
    root = Path(args.ProjectRoot)
    checks = [
        (root / "app/templates/corporate_information_center/recipients.html", [MARKER, "data-recipient-page", "data-rec-action", "manager_ids", "staff_ids"]),
        (root / "app/static/css/corporate_information_center_recipients_pro_v1.css", [MARKER, "cic-rec-page", "cic-rec-person-card"]),
        (root / "app/static/js/corporate_information_center_recipients_pro_v1.js", [MARKER, "select-visible-staff", "applyFilters"]),
    ]
    errors = []
    for path, needles in checks:
        if not path.exists():
            errors.append(f"Eksik dosya: {path}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "\\n" in text[:300]:
            errors.append(f"Kaçışlı newline kalıntısı var: {path}")
        for n in needles:
            if n not in text:
                errors.append(f"{path} içinde eksik ifade: {n}")
    if errors:
        print("BYS360_CIC_V3_0_RECIPIENTS_PRO_USABILITY_V1_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 1
    print("BYS360_CIC_V3_0_RECIPIENTS_PRO_USABILITY_V1_GATE_OK")
    print("BYS360_CIC_V3_0_RECIPIENTS_PRO_USABILITY_V1_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
