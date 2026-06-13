# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import ast
from pathlib import Path

MARKER = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default=r"C:\bys360\project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)
    errors: list[str] = []

    repair = root / "scripts" / "communication" / "repair_corporate_information_center_v3_0_phase7_11_template_compat_fix.py"
    check = root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_11_template_compat_fix.py"
    for py in [repair, check]:
        if not py.exists():
            errors.append(f"Eksik Python dosyası: {py}")
        else:
            try:
                ast.parse(read_text(py))
            except SyntaxError as exc:
                errors.append(f"Python sözdizimi hatası: {py.name}: {exc}")

    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    if not base.exists():
        errors.append("Eksik dosya: corporate_information_center/base.html")
    else:
        text = read_text(base)
        required = ["{% macro cic_csrf", "{% macro status_pill", MARKER]
        for item in required:
            if item not in text:
                errors.append(f"base.html içinde eksik ifade: {item}")
        if "\\n" in text and text.count("\n") < 8:
            errors.append("base.html hâlâ literal \\n kaçışları içeriyor")
        if "url_for(\\'static" in text or "\\\"static" in text:
            errors.append("base.html içinde kaçışlı url_for/static kalıntısı var")

    logs = root / "app" / "templates" / "corporate_information_center" / "logs.html"
    if logs.exists():
        lt = read_text(logs)
        if "phase6.log_quality.items" in lt:
            errors.append("logs.html içinde phase6.log_quality.items hâlâ güvenli değil")

    if errors:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX_GATE_FAIL")
        for err in errors:
            print("HATA: " + err)
        return 2
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX_GATE_OK")
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_11_TEMPLATE_COMPAT_FIX_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
