from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

VERSION = "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_RESUME_V2"


def read(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", "-ProjectRoot", dest="project_root", default=".")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    errors: list[str] = []

    template_dir = root / "app" / "templates" / "corporate_information_center"
    required_templates = [
        "base.html", "overview.html", "tasks.html", "recipients.html",
        "templates.html", "test.html", "logs.html", "system.html",
    ]
    for name in required_templates:
        path = template_dir / name
        if not path.exists():
            errors.append(f"Eksik template: {path}")
            continue
        text = read(path)
        if "\\n" in text[:800]:
            errors.append(f"{name} içinde literal \\n kalıntısı var")
        if "{{ url_for(\\'static\\'" in text or "\\'" in text[:1200]:
            errors.append(f"{name} içinde kaçışlı Jinja tırnak kalıntısı var")

    base = read(template_dir / "base.html") if (template_dir / "base.html").exists() else ""
    for marker in ("cic_csrf", "status_pill", "task_status", "user_initial", "user_full_name"):
        if marker not in base:
            errors.append(f"base.html içinde ortak makro/yardımcı eksik: {marker}")

    for name in ("tasks.html", "recipients.html", "templates.html", "system.html", "test.html"):
        path = template_dir / name
        if path.exists():
            text = read(path)
            if "method=\"post\"" in text.lower() or "method='post'" in text.lower():
                if "csrf_token" not in text and "cic_csrf" not in text:
                    errors.append(f"{name} POST form içeriyor ama CSRF token/makro yok")

    log_tpl = template_dir / "logs.html"
    tmpl_tpl = template_dir / "templates.html"
    for path in (log_tpl, tmpl_tpl):
        if path.exists():
            text = read(path)
            if ".items %}" in text:
                errors.append(f"{path.name} içinde .items iterable hatası riski var")

    # En azından temel Python dosyaları derlenebilir olmalı.
    for rel in ("app/__init__.py", "app/communication/corporate_information_center_routes.py", "app/services/corporate_information_center.py"):
        path = root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                errors.append(f"Python compile hatası: {rel}: {exc}")

    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 1

    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
