# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path
from jinja2 import Environment

MARKER = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_10_STATUS_PILL_FIX"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_template(path: Path) -> None:
    Environment().parse(read(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default=r"C:\bys360\project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    if not base.exists():
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_10_STATUS_PILL_FIX_GATE_FAIL")
        print(f"HATA: base.html bulunamadı: {base}")
        return 2
    text = read(base)
    errors = []
    if "{% macro status_pill" not in text:
        errors.append("base.html içinde status_pill makrosu yok")
    if MARKER not in text:
        errors.append("Faz 7.10 imzası yok")
    if "\\n" in text[:500]:
        errors.append("base.html başında literal \\n kalıntısı var")
    for path in sorted((root / "app" / "templates" / "corporate_information_center").glob("*.html")):
        try:
            parse_template(path)
        except Exception as exc:
            errors.append(f"Jinja parse hatası: {path.name}: {exc}")
    for path in sorted((root / "app" / "templates" / "corporate_information_center").glob("*.html")):
        t = read(path)
        if "status_pill(" in t and "{% macro status_pill" not in t and path.name != "base.html":
            # Makro parent base içinde var; bu bilgi engelleyici değil. Alt template içinde de güvenli eklenmiş olmalı.
            errors.append(f"{path.name} status_pill kullanıyor ama kendi güvenli makrosu yok")
    if errors:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_10_STATUS_PILL_FIX_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 2
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_10_STATUS_PILL_FIX_GATE_OK")
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_10_STATUS_PILL_FIX_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
