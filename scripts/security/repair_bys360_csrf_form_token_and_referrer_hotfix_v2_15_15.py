from __future__ import annotations

import argparse
import datetime as _dt
import py_compile
import re
import shutil
from pathlib import Path

VERSION = "BYS360_CSRF_FORM_TOKEN_AND_REFERRER_HOTFIX_V2_15_15"
CSRF_INPUT = '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'

NEW_CSRF_HANDLER = '''    @app.errorhandler(CSRFError)
    def bys360_b77_handle_csrf_error(error):  # noqa: ANN001, ANN202
        msg = "Güvenlik doğrulaması yenilendi. Lütfen sayfayı yenileyip tekrar deneyin."
        wants_json = (
            request.path.startswith("/api/")
            or request.is_json
            or "application/json" in (request.headers.get("Accept") or "")
        )
        if wants_json:
            return jsonify({"ok": False, "success": False, "message": msg, "code": "csrf_refresh_required"}), 400
        try:
            flash(msg, "warning")
        except Exception:
            pass

        # BYS360_CSRF_FORM_TOKEN_AND_REFERRER_HOTFIX_V2_15_15
        # Kurumsal ekranlarda CSRF süresi dolarsa kullanıcı login/home'a savrulmasın;
        # geldiği ekrana güvenli şekilde dönsün. Böylece mail test gibi POST ekranları
        # kullanıcı dostu biçimde yeniden denenebilir.
        try:
            referrer = request.referrer or ""
            host_url = (request.host_url or "").rstrip("/")
            if referrer and (referrer.startswith(host_url) or referrer.startswith("/")):
                return redirect(referrer)
            if request.path.startswith("/dashboard/"):
                return redirect(request.path)
        except Exception:
            pass

        # Projede gerçek login endpoint'i main.login. auth.login / login olmayan kurulumlarda
        # CSRF hatası ikinci bir BuildError'a dönüşmemeli.
        for endpoint in ("main.login", "auth.login", "login"):
            try:
                return redirect(url_for(endpoint))
            except Exception:
                continue
        return redirect("/login")
'''


def _read(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def backup(path: Path, root: Path) -> Path:
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = root / ".backup" / "bys360_csrf_form_token_referrer_hotfix_v2_15_15" / ts
    bdir.mkdir(parents=True, exist_ok=True)
    target = bdir / path.relative_to(root).as_posix().replace("/", "__")
    shutil.copy2(path, target)
    return target


def _has_token_near(text: str, pos: int) -> bool:
    window = text[pos:pos + 900]
    return 'name="csrf_token"' in window or "name='csrf_token'" in window or "csrf_token()" in window


def add_csrf_tokens_to_template(path: Path, root: Path) -> bool:
    if not path.exists():
        return False
    text = _read(path)
    original = text
    lower = text.lower()
    if "<form" not in lower or ('method="post"' not in lower and "method='post'" not in lower):
        return False

    form_re = re.compile(r"<form\b(?=[^>]*\bmethod\s*=\s*['\"]post['\"])[^>]*>", re.IGNORECASE)
    parts: list[str] = []
    last = 0
    changed = False
    for m in form_re.finditer(text):
        parts.append(text[last:m.end()])
        if not _has_token_near(text, m.end()):
            parts.append("\n    " + CSRF_INPUT)
            changed = True
        last = m.end()
    parts.append(text[last:])
    text = "".join(parts)
    if changed and VERSION not in text:
        text = text.replace("{% block cic_content %}", "{% block cic_content %}\n<!-- " + VERSION + " -->", 1)
    if text != original:
        backup(path, root)
        _write(path, text)
        return True
    return False


def patch_cic_templates(root: Path) -> list[Path]:
    changed: list[Path] = []
    base = root / "app" / "templates" / "corporate_information_center"
    for name in ("tasks.html", "recipients.html", "templates.html", "system.html", "test.html"):
        path = base / name
        if add_csrf_tokens_to_template(path, root):
            changed.append(path)
    return changed


def patch_app_init(root: Path) -> bool:
    path = root / "app" / "__init__.py"
    if not path.exists():
        raise FileNotFoundError(f"Bulunamadı: {path}")
    text = _read(path)
    original = text

    pattern = re.compile(
        r"    @app\.errorhandler\(CSRFError\)\n"
        r"    def bys360_b77_handle_csrf_error\(error\):  # noqa: ANN001, ANN202\n"
        r".*?"
        r"        return redirect\(\"/login\"\)\n",
        re.DOTALL,
    )
    text2, count = pattern.subn(NEW_CSRF_HANDLER, text, count=1)

    if count == 0:
        text2 = text
        text2 = text2.replace(
            'for endpoint in ("auth.login", "login", "main.login"):',
            'for endpoint in ("main.login", "auth.login", "login"):',
        )
        text2 = text2.replace(
            "for endpoint in ('auth.login', 'login', 'main.login'):",
            "for endpoint in ('main.login', 'auth.login', 'login'):",
        )
        marker = '        for endpoint in ("main.login", "auth.login", "login"):'
        if marker in text2 and VERSION not in text2:
            block = '''        # BYS360_CSRF_FORM_TOKEN_AND_REFERRER_HOTFIX_V2_15_15
        try:
            referrer = request.referrer or ""
            host_url = (request.host_url or "").rstrip("/")
            if referrer and (referrer.startswith(host_url) or referrer.startswith("/")):
                return redirect(referrer)
            if request.path.startswith("/dashboard/"):
                return redirect(request.path)
        except Exception:
            pass

'''
            text2 = text2.replace(marker, block + marker, 1)

    if text2 != original:
        backup(path, root)
        _write(path, text2)
        return True
    return False


def gate(root: Path) -> list[str]:
    errors: list[str] = []
    init_path = root / "app" / "__init__.py"
    init_text = _read(init_path) if init_path.exists() else ""
    if VERSION not in init_text:
        errors.append("app/__init__.py içinde V2.15.15 referrer CSRF hotfix etiketi yok")
    if 'for endpoint in ("main.login", "auth.login", "login")' not in init_text and "for endpoint in ('main.login', 'auth.login', 'login')" not in init_text:
        errors.append("CSRF login endpoint sırası main.login ile başlamıyor")
    if 'request.referrer' not in init_text or 'request.path.startswith("/dashboard/")' not in init_text:
        errors.append("CSRF handler dashboard/referrer dönüş mantığı eksik")
    if "BYS360 kalite denetimi: except bloğu loglandı (app/__init__.py:111)" in init_text:
        errors.append("CSRF handler içinde eski gereksiz exception logu hâlâ duruyor")

    template_base = root / "app" / "templates" / "corporate_information_center"
    for name in ("tasks.html", "recipients.html", "templates.html", "system.html", "test.html"):
        path = template_base / name
        if not path.exists():
            errors.append(f"Eksik şablon: {path}")
            continue
        text = _read(path)
        post_form_count = len(re.findall(r"<form\b(?=[^>]*\bmethod\s*=\s*['\"]post['\"])[^>]*>", text, flags=re.IGNORECASE))
        token_count = text.count('name="csrf_token"') + text.count("name='csrf_token'")
        if post_form_count and token_count < post_form_count:
            errors.append(f"{name} içinde POST form sayısı kadar CSRF token yok: form={post_form_count}, token={token_count}")
        if name == "test.html" and "csrf_token()" not in text:
            errors.append("test.html mail test formunda csrf_token() eksik")
    try:
        py_compile.compile(str(init_path), doraise=True)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"app/__init__.py compile hatası: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", "-ProjectRoot", dest="project_root", default=".")
    parser.add_argument("--mode", "-Mode", dest="mode", default="all")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    print(f"{VERSION} uygulanıyor...")
    print(f"ProjectRoot={root}")

    changed_templates = patch_cic_templates(root)
    changed_init = patch_app_init(root)

    if changed_templates or changed_init:
        print(f"{VERSION}_APPLY_OK")
        print("Güncellenen dosyalar:")
        if changed_init:
            print(" - app\\__init__.py")
        for p in changed_templates:
            print(" - " + str(p.relative_to(root)).replace("/", "\\"))
    else:
        print(f"{VERSION}_APPLY_NO_CHANGE")

    errors = gate(root)
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
