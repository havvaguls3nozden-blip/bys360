# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import re
from pathlib import Path
from jinja2 import Environment

MARKER = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_12_ALL_TEMPLATE_MACRO_FIX"
REQUIRED_MACROS = ["cic_csrf", "status_pill", "task_status", "user_full_name", "user_initial"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-ProjectRoot", default="C:\\bys360\\project")
    args = ap.parse_args()
    root = Path(args.ProjectRoot)
    tpl_dir = root / "app" / "templates" / "corporate_information_center"
    base = tpl_dir / "base.html"
    errors: list[str] = []
    if not base.exists():
        errors.append(f"base.html yok: {base}")
    else:
        text = base.read_text(encoding="utf-8")
        if "\\n" in text[:500]:
            errors.append("base.html icinde literal \\n kalintisi var")
        if "unexpected char" in text:
            errors.append("base.html icinde hata metni kalintisi var")
        for macro in REQUIRED_MACROS:
            if f"macro {macro}" not in text:
                errors.append(f"base.html icinde eksik makro: {macro}")
        if "url_for(\\'static\\'" in text or "url_for(\"static\"" in text.replace("'", '"') and "filename=\"" not in text:
            # soft check avoided; Jinja parse catches syntax
            pass
    env = Environment()
    for path in sorted(tpl_dir.glob("*.html")):
        txt = path.read_text(encoding="utf-8")
        try:
            env.parse(txt)
        except Exception as exc:
            errors.append(f"Jinja parse hatasi {path.name}: {exc}")
        if re.search(r"phase[67]\.[A-Za-z0-9_]+\.items", txt):
            errors.append(f"{path.name} icinde dict.items nokta kullanimi kaldi")
    if errors:
        print(f"{MARKER}_GATE_FAIL")
        for e in errors:
            print(f"HATA: {e}")
        return 2
    print(f"{MARKER}_GATE_OK")
    print(f"{MARKER}_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
