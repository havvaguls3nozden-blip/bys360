from __future__ import annotations
import argparse, re, shutil
from datetime import datetime
from pathlib import Path

CSS_NAME = "corporate_information_center_v4_6b_celebrations_final.css"
JS_NAME = "corporate_information_center_v4_6b_celebrations_final.js"


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "cp1252"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def backup(path: Path, root: Path) -> None:
    if not path.exists():
        return
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = root / "backups" / f"bys360_cic_v4_6b_template_final_{stamp}" / path.relative_to(root).parent
    bdir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, bdir / path.name)


def ensure_css_ref(text: str) -> str:
    if CSS_NAME in text:
        return text
    line = "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/" + CSS_NAME + "') }}?v=4_6b\">"
    if "{% block extra_head %}" in text:
        return text.replace("{% block extra_head %}", "{% block extra_head %}\n" + line, 1)
    return text + "\n{% block extra_head %}\n" + line + "\n{{ super() }}\n{% endblock %}\n"


def ensure_js_ref(text: str) -> str:
    if JS_NAME in text:
        return text
    line = "<script src=\"{{ url_for('static', filename='js/" + JS_NAME + "') }}?v=4_6b\"></script>"
    if "{% block extra_scripts %}" in text:
        return text.replace("{% block extra_scripts %}", "{% block extra_scripts %}\n" + line, 1)
    return text + "\n{% block extra_scripts %}\n" + line + "\n{{ super() }}\n{% endblock %}\n"


def fix_base(base: Path, root: Path) -> None:
    if not base.exists():
        return
    backup(base, root)
    text = read_text(base)
    text = re.sub(r"\{% block title %\}Kurumsal Bilgilendirme Merkezi \| BYS360\s*<link[^>]+corporate_information_center_v4_6_celebrations_studio\.css[^>]*>\s*\{% endblock %\}", "{% block title %}Kurumsal Bilgilendirme Merkezi | BYS360{% endblock %}", text)
    text = re.sub(r"(\{% block title %\}[^\n]*?BYS360)\s*<link[^>]+corporate_information_center_[^>]+>\s*(\{% endblock %\})", r"\1\2", text)
    text = ensure_css_ref(text)
    text = ensure_js_ref(text)
    text = text.replace("pilot test", "ön kontrol").replace("Pilot test", "Ön kontrol").replace("kuru çalışma", "ön kontrol").replace("Kuru çalışma", "Ön kontrol")
    base.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    here = Path(__file__).resolve().parent
    assets = here / "assets"
    tpl = root / "app" / "templates" / "corporate_information_center" / "celebrations.html"
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    css = root / "app" / "static" / "css" / CSS_NAME
    js = root / "app" / "static" / "js" / JS_NAME
    tpl.parent.mkdir(parents=True, exist_ok=True)
    css.parent.mkdir(parents=True, exist_ok=True)
    js.parent.mkdir(parents=True, exist_ok=True)
    backup(tpl, root)
    shutil.copy2(assets / "celebrations.html", tpl)
    shutil.copy2(assets / CSS_NAME, css)
    shutil.copy2(assets / JS_NAME, js)
    fix_base(base, root)
    try:
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader(str(root / "app" / "templates")))
        env.get_template("corporate_information_center/celebrations.html")
        env.get_template("corporate_information_center/base.html")
    except Exception as exc:
        raise SystemExit(f"BYS360_CIC_V4_6B_TEMPLATE_PARSE_FAIL={exc!r}")
    print("BYS360_CIC_V4_6B_CELEBRATIONS_TEMPLATE_FINAL_FIX_APPLY_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
