from __future__ import annotations
import argparse
import ast
from pathlib import Path

VERSION = "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V4"

def read(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-ProjectRoot", default=r"C:\bys360\project")
    args = ap.parse_args()
    root = Path(args.ProjectRoot)
    errors: list[str] = []
    required = [
        "app/services/corporate_information_center.py",
        "app/communication/corporate_information_center_routes.py",
        "app/templates/corporate_information_center/base.html",
        "app/templates/corporate_information_center/overview.html",
        "app/templates/corporate_information_center/tasks.html",
        "app/templates/corporate_information_center/recipients.html",
        "app/templates/corporate_information_center/templates.html",
        "app/templates/corporate_information_center/test.html",
        "app/templates/corporate_information_center/logs.html",
        "app/templates/corporate_information_center/system.html",
    ]
    for rel in required:
        if not (root / rel).exists():
            errors.append(f"Eksik dosya: {root / rel}")
    base = root / "app/templates/corporate_information_center/base.html"
    if base.exists():
        txt = read(base)
        needles = ["cic_csrf", "status_pill", "task_status", "user_initial", "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_12_ALL_TEMPLATE_MACRO_FIX"]
        for n in needles:
            if n not in txt:
                errors.append(f"base.html içinde eksik ifade: {n}")
        if "\
" in txt[:500] or "url_for(\\'static" in txt:
            errors.append("base.html içinde kaçışlı newline/tırnak kalıntısı var")
    route = root / "app/communication/corporate_information_center_routes.py"
    if route.exists():
        text = read(route)
        for n in ["corporate_information_center_overview", "corporate_information_center_tasks", "corporate_information_center_recipients", "corporate_information_center_test"]:
            if n not in text:
                errors.append(f"route dosyasında eksik ifade: {n}")
        try:
            ast.parse(text)
        except SyntaxError as e:
            errors.append(f"route syntax hatasi: {e}")
    service = root / "app/services/corporate_information_center.py"
    if service.exists():
        text = read(service)
        for n in ["def context(", "def send_task(", "TASK_DEFINITIONS"]:
            if n not in text:
                errors.append(f"service dosyasında eksik ifade: {n}")
        try:
            ast.parse(text)
        except SyntaxError as e:
            errors.append(f"service syntax hatasi: {e}")
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 1
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
