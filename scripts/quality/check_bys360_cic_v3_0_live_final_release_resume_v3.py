from __future__ import annotations
import argparse
import py_compile
from pathlib import Path

CODE = "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V3"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-ProjectRoot", default="C:\\bys360\\project")
    args = ap.parse_args()
    root = Path(args.ProjectRoot)
    errors: list[str] = []

    service = root / "app/services/corporate_information_center.py"
    if not service.exists():
        errors.append(f"Eksik servis dosyası: {service}")
    else:
        text = read(service)
        for needle in ["TASK_DEFINITIONS", "def send_task(", "def context(", "def ensure_defaults("]:
            if needle not in text:
                errors.append(f"Servis dosyasında eksik ifade: {needle}")
        try:
            py_compile.compile(str(service), doraise=True)
        except Exception as exc:
            errors.append(f"Servis Python derleme hatası: {exc}")

    tpl_dir = root / "app/templates/corporate_information_center"
    required = ["base.html", "overview.html", "tasks.html", "recipients.html", "templates.html", "test.html", "logs.html", "system.html"]
    for name in required:
        p = tpl_dir / name
        if not p.exists():
            errors.append(f"Eksik şablon: {p}")
    base = tpl_dir / "base.html"
    if base.exists():
        b = read(base)
        for needle in ["macro cic_csrf", "macro status_pill", "macro task_status", "macro user_initial", "macro user_full_name", "block cic_content"]:
            if needle not in b:
                errors.append(f"base.html içinde eksik makro/blok: {needle}")
        if "\\n{%" in b[:500] or "url_for(\\'static" in b:
            errors.append("base.html içinde kaçışlı newline/tırnak kalıntısı var")

    # Jinja kaynaklarında bilinen items kullanım hatası kalmamalı.
    for rel in ["templates.html", "logs.html"]:
        p = tpl_dir / rel
        if p.exists():
            t = read(p)
            if ".items %}" in t or ".items</" in t:
                errors.append(f"{rel} içinde .items iterasyon kalıntısı var")

    routes = root / "app/communication/corporate_information_center_routes.py"
    if not routes.exists():
        errors.append(f"Eksik route dosyası: {routes}")
    else:
        try:
            py_compile.compile(str(routes), doraise=True)
        except Exception as exc:
            errors.append(f"Route Python derleme hatası: {exc}")

    if errors:
        print(f"{CODE}_GATE_FAIL")
        for e in errors:
            print("HATA:", e)
        return 1
    print(f"{CODE}_GATE_OK")
    print(f"{CODE}_FINAL_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
