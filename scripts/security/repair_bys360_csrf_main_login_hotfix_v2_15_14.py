from __future__ import annotations

import argparse
import datetime as _dt
import py_compile
import re
import shutil
from pathlib import Path

VERSION = "BYS360_CSRF_MAIN_LOGIN_HOTFIX_V2_15_14"

NEW_BLOCK = '''    @app.errorhandler(CSRFError)
    def bys360_b77_handle_csrf_error(error):  # noqa: ANN001, ANN202
        msg = "Güvenlik doğrulaması yenilendi. Lütfen sayfayı yenileyip tekrar giriş yapın."
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

        # BYS360_CSRF_MAIN_LOGIN_HOTFIX_V2_15_14
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
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def backup(path: Path, root: Path) -> Path:
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = root / ".backup" / "bys360_csrf_main_login_hotfix_v2_15_14" / ts
    bdir.mkdir(parents=True, exist_ok=True)
    target = bdir / path.relative_to(root).as_posix().replace("/", "__")
    shutil.copy2(path, target)
    return target


def patch_app_init(root: Path) -> bool:
    path = root / "app" / "__init__.py"
    if not path.exists():
        raise FileNotFoundError(f"Bulunamadi: {path}")
    text = _read(path)
    original = text

    pattern = re.compile(
        r"    @app\.errorhandler\(CSRFError\)\n"
        r"    def bys360_b77_handle_csrf_error\(error\):  # noqa: ANN001, ANN202\n"
        r".*?"
        r"        return redirect\(\"/login\"\)\n",
        re.DOTALL,
    )
    text2, count = pattern.subn(NEW_BLOCK, text, count=1)

    if count == 0:
        # Conservative fallback for slightly different copies.
        text2 = text
        text2 = text2.replace(
            'for endpoint in ("auth.login", "login", "main.login"):',
            'for endpoint in ("main.login", "auth.login", "login"):',
        )
        text2 = text2.replace(
            "for endpoint in ('auth.login', 'login', 'main.login'):",
            "for endpoint in ('main.login', 'auth.login', 'login'):",
        )
        text2 = text2.replace("url_for(\"auth.login\")", "url_for(\"main.login\")")
        text2 = text2.replace("url_for('auth.login')", "url_for('main.login')")
        text2 = text2.replace("url_for(\"login\")", "url_for(\"main.login\")")
        text2 = text2.replace("url_for('login')", "url_for('main.login')")
        text2 = text2.replace(
            '                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/__init__.py:111)")\n',
            '',
        )

    if text2 != original:
        backup(path, root)
        _write(path, text2)
        return True
    return False


def gate(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / "app" / "__init__.py"
    text = _read(path) if path.exists() else ""
    if 'BYS360_CSRF_MAIN_LOGIN_HOTFIX_V2_15_14' not in text:
        errors.append("app/__init__.py CSRF hotfix etiketi bulunamadi")
    if 'for endpoint in ("main.login", "auth.login", "login")' not in text and "for endpoint in ('main.login', 'auth.login', 'login')" not in text:
        errors.append("CSRF login endpoint sirasi main.login ile baslamiyor")
    if 'for endpoint in ("auth.login", "login", "main.login")' in text or "for endpoint in ('auth.login', 'login', 'main.login')" in text:
        errors.append("Eski hatali CSRF endpoint sirasi hala duruyor")
    if "BYS360 kalite denetimi: except bloğu loglandı (app/__init__.py:111)" in text:
        errors.append("CSRF handler icinde gereksiz exception logu hala duruyor")
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"app/__init__.py compile hatasi: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", "-ProjectRoot", dest="project_root", default=".")
    parser.add_argument("--mode", "-Mode", dest="mode", default="all")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    print(f"{VERSION} uygulanıyor...")
    print(f"ProjectRoot={root}")
    changed = patch_app_init(root)
    if changed:
        print(f"{VERSION}_APPLY_OK")
        print("Guncellenen dosyalar:")
        print(" - app\\__init__.py")
    else:
        print(f"{VERSION}_APPLY_NO_CHANGE")
    errors = gate(root)
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for e in errors:
            print(f"HATA: {e}")
        return 1
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
