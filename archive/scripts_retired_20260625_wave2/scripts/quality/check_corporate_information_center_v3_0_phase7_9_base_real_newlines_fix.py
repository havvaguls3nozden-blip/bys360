# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from pathlib import Path
from jinja2 import Environment

PHASE = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_9_BASE_REAL_NEWLINES_FIX"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("-ProjectRoot", default="C:/bys360/project")
    args = p.parse_args()
    root = Path(args.ProjectRoot)
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    css = root / "app" / "static" / "css" / "corporate_information_center_v3_0_phase7_9_base_clean.css"
    text = base.read_text(encoding="utf-8")
    errors = []
    if PHASE not in text:
        errors.append("base.html içinde Faz 7.9 imzası yok")
    if "\\n" in text[:2000]:
        errors.append("base.html içinde literal \\n kalıntısı var")
    if "\\'" in text:
        errors.append("base.html içinde kaçışlı tırnak kalıntısı var")
    if "url_for('static', filename='css/corporate_information_center_v3_0_phase7_9_base_clean.css')" not in text:
        errors.append("Faz 7.9 CSS linki yok")
    if not css.exists():
        errors.append("Faz 7.9 CSS dosyası yok")
    try:
        Environment().parse(text)
    except Exception as exc:
        errors.append(f"Jinja parse hatası: {exc}")
    if errors:
        print(f"{PHASE}_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 2
    print(f"{PHASE}_GATE_OK")
    print(f"{PHASE}_FINAL_OK")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
