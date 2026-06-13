from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

VERSION = "BYS360_LOGOUT_FORCE_CLEAR_V2_15_12"

HELPER_BLOCK = r'''
# BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_BEGIN
def _bys360_unique_values(values):
    seen = set()
    result = []
    for value in values:
        if value is None:
            key = "__none__"
            normalized = None
        else:
            normalized = str(value).strip()
            if not normalized:
                continue
            key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized if key != "__none__" else None)
    return result


def _bys360_auth_cookie_domains():
    host = (request.host or "").split(":", 1)[0].strip().lower()
    configured = current_app.config.get("SESSION_COOKIE_DOMAIN")
    domains = [None, configured]
    if host and host not in {"localhost", "127.0.0.1", "::1"}:
        domains.append(host)
        parts = [part for part in host.split(".") if part]
        if len(parts) >= 2:
            domains.append("." + ".".join(parts[-2:]))
        if len(parts) >= 3:
            domains.append("." + ".".join(parts[-3:]))
    return _bys360_unique_values(domains)


def _bys360_delete_auth_cookies(response):
    cookie_names = _bys360_unique_values([
        current_app.config.get("SESSION_COOKIE_NAME") or "session",
        current_app.config.get("REMEMBER_COOKIE_NAME") or "remember_token",
        "session",
        "remember_token",
        "bys360_session",
        "bys360_remember_token",
    ])
    cookie_paths = _bys360_unique_values(["/", current_app.config.get("APPLICATION_ROOT") or "/"])
    for name in cookie_names:
        for path in cookie_paths:
            for domain in _bys360_auth_cookie_domains():
                try:
                    response.delete_cookie(name, path=path, domain=domain)
                except TypeError:
                    response.delete_cookie(name, path=path)
                except Exception:
                    current_app.logger.debug(
                        "Logout cookie temizleme atlandı | name=%s | domain=%s | path=%s",
                        name,
                        domain,
                        path,
                    )
    return response


def _bys360_no_store_response(response):
    response.headers["Cache-Control"] = "no-store, no-cache, max-age=0, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Clear-Site-Data"] = '"cache"'
    response.headers["X-BYS360-Logout-Fix"] = "V2.15.12"
    return response
# BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_END
'''.strip()

LOGOUT_FUNCTION = r'''
def logout():
    try:
        _reset_auth_challenge_state()
    except Exception:
        current_app.logger.debug("Logout auth challenge temizliği atlandı", exc_info=True)

    try:
        logout_user()
    except Exception:
        current_app.logger.debug("Flask-Login logout_user atlandı", exc_info=True)

    try:
        session.clear()
        session.permanent = False
        session.modified = True
    except Exception:
        current_app.logger.debug("Logout session temizliği atlandı", exc_info=True)

    response = make_response(redirect(url_for("main.login")))
    _bys360_delete_auth_cookies(response)
    _bys360_no_store_response(response)
    return response
'''.strip()

NO_STORE_BLOCK = r'''
# BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_BEGIN
@main_bp.after_app_request
def bys360_logout_no_store_authenticated_pages(response):
    try:
        endpoint = str(getattr(request, "endpoint", "") or "")
        path = str(getattr(request, "path", "") or "")
        content_type = str(response.headers.get("Content-Type", "") or "")
        wants_html = "text/html" in content_type or "text/html" in str(request.headers.get("Accept", "") or "")
        sensitive_path = (
            path in {"/", "/home", "/login", "/logout"}
            or path.startswith((
                "/account", "/admin", "/dashboard", "/feedback", "/hr-management",
                "/messages", "/performance", "/performans", "/personnel", "/portal",
                "/settings", "/support", "/survey", "/surveys",
            ))
        )
        if endpoint != "static" and (wants_html or sensitive_path) and (sensitive_path or current_user.is_authenticated):
            response.headers["Cache-Control"] = "no-store, no-cache, max-age=0, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers.setdefault("X-BYS360-Logout-Fix", "V2.15.12")
    except Exception:
        current_app.logger.debug("BYS360 logout no-store header uygulanamadı", exc_info=True)
    return response
# BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_END
'''.strip()

ERROR_HELPER_BLOCK = r'''
# BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_BEGIN
def _bys360_csrf_logout_cookie_domains():
    host = (request.host or "").split(":", 1)[0].strip().lower()
    configured = current_app.config.get("SESSION_COOKIE_DOMAIN")
    domains = [None, configured]
    if host and host not in {"localhost", "127.0.0.1", "::1"}:
        domains.append(host)
        parts = [part for part in host.split(".") if part]
        if len(parts) >= 2:
            domains.append("." + ".".join(parts[-2:]))
        if len(parts) >= 3:
            domains.append("." + ".".join(parts[-3:]))
    seen = set()
    out = []
    for item in domains:
        key = "__none__" if item is None else str(item).lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _bys360_csrf_logout_delete_auth_cookies(response):
    cookie_names = [
        current_app.config.get("SESSION_COOKIE_NAME") or "session",
        current_app.config.get("REMEMBER_COOKIE_NAME") or "remember_token",
        "session",
        "remember_token",
        "bys360_session",
        "bys360_remember_token",
    ]
    cookie_names = list(dict.fromkeys([str(x) for x in cookie_names if x]))
    cookie_paths = list(dict.fromkeys(["/", current_app.config.get("APPLICATION_ROOT") or "/"]))
    for name in cookie_names:
        for path in cookie_paths:
            for domain in _bys360_csrf_logout_cookie_domains():
                try:
                    response.delete_cookie(name, path=path, domain=domain)
                except TypeError:
                    response.delete_cookie(name, path=path)
                except Exception:
                    current_app.logger.debug("CSRF logout cookie temizleme atlandı", exc_info=True)
    response.headers["Cache-Control"] = "no-store, no-cache, max-age=0, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Clear-Site-Data"] = '"cache"'
    response.headers["X-BYS360-Logout-Fix"] = "V2.15.12-CSRF"
    return response
# BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_END
'''.strip()

BASE_LOGOUT_BLOCK = r'''
<!-- BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_BEGIN -->
<form id="bys360LogoutForceClearForm" action="/logout" method="post" style="display:none;">
    {% if csrf_token is defined %}
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    {% endif %}
</form>
<script>
(function () {
    "use strict";
    var formId = "bys360LogoutForceClearForm";
    function isLogoutUrl(value) {
        if (!value) return false;
        try {
            var url = new URL(value, window.location.origin);
            return url.pathname.replace(/\/+$/, "") === "/logout";
        } catch (error) {
            return value === "/logout" || /\/logout\/?$/.test(String(value));
        }
    }
    function clearLightClientState() {
        try { window.sessionStorage && window.sessionStorage.clear(); } catch (error) {}
        try {
            if (window.caches && window.caches.keys) {
                window.caches.keys().then(function (keys) {
                    keys.forEach(function (key) {
                        if (/bys360/i.test(key)) window.caches.delete(key);
                    });
                }).catch(function () {});
            }
        } catch (error) {}
    }
    function postLogout(event) {
        if (event && typeof event.preventDefault === "function") event.preventDefault();
        clearLightClientState();
        var form = document.getElementById(formId) || document.getElementById("logoutForm") || document.getElementById("bys360LogoutPostForm");
        if (form) {
            try { form.submit(); return false; } catch (error) {}
        }
        window.location.assign("/logout");
        return false;
    }
    window.bys360ForceLogout = postLogout;
    window.submitLogoutForm = postLogout;
    document.addEventListener("click", function (event) {
        var target = event.target && event.target.closest ? event.target.closest("a[href],button[data-logout]") : null;
        if (!target) return;
        var href = target.getAttribute("href") || target.getAttribute("data-logout") || "";
        if (!isLogoutUrl(href)) return;
        postLogout(event);
    }, true);
    window.addEventListener("pageshow", function (event) {
        if (event && event.persisted && /\/logout\/?$/.test(window.location.pathname)) {
            window.location.replace("/login");
        }
    });
})();
</script>
<!-- BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_END -->
'''.strip()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def backup(path: Path, suffix: str = ".logout_v2_15_12.bak") -> None:
    bak = path.with_suffix(path.suffix + suffix)
    if not bak.exists():
        shutil.copy2(path, bak)


def remove_marker_blocks(text: str, marker: str, kind: str = "python") -> str:
    if kind == "html":
        pattern = re.compile(
            rf"\n?<!-- {re.escape(marker)}_BEGIN -->\n.*?\n<!-- {re.escape(marker)}_END -->\n?",
            re.DOTALL,
        )
    else:
        pattern = re.compile(
            rf"\n?# {re.escape(marker)}_BEGIN\n.*?\n# {re.escape(marker)}_END\n?",
            re.DOTALL,
        )
    return pattern.sub("\n", text)


def ensure_flask_import(text: str, name: str) -> str:
    pattern = re.compile(r"^from flask import (?P<items>[^\n]+)$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return "from flask import " + name + "\n" + text
    items = [item.strip() for item in match.group("items").split(",") if item.strip()]
    if name not in items:
        items.append(name)
        items = sorted(set(items), key=lambda x: x.lower())
        text = text[:match.start()] + "from flask import " + ", ".join(items) + text[match.end():]
    return text


def patch_auth_routes(project_root: Path) -> list[str]:
    path = project_root / "app" / "auth" / "routes.py"
    text = read_text(path)
    original = text

    text = re.sub(
        r'@main_bp\.route\(\s*["\']/logout["\'][^\n]*\)',
        '@main_bp.route("/logout", methods=["GET", "POST"])',
        text,
        count=1,
    )
    text = re.sub(
        r'(@main_bp\.route\(\s*["\']/logout["\'][^\n]*\)\s*\n)\s*@login_required\s*\n(\s*def\s+logout\s*\()',
        r'\1\2',
        text,
        count=1,
    )

    if text != original:
        backup(path)
        write_text(path, text)
        return [str(path.relative_to(project_root))]
    return []


def patch_auth_handler(project_root: Path) -> list[str]:
    path = project_root / "app" / "main_handlers" / "auth_handlers.py"
    text = read_text(path)
    original = text

    text = ensure_flask_import(text, "make_response")
    for marker in [
        "BYS360_LIVE_LOGOUT_FORCE_CLEAR_V2_13_3",
        "BYS360_LIVE_LOGOUT_FORCE_CLEAR_V2_13_4",
        "BYS360_LOGOUT_FORCE_CLEAR_V2_15_12",
    ]:
        text = remove_marker_blocks(text, marker)

    start = text.find("\ndef logout():")
    if start == -1:
        start = text.find("def logout():")
    if start == -1:
        raise RuntimeError("auth_handlers.py içinde def logout() bulunamadı.")
    end = text.find("\ndef setup_admin", start)
    if end == -1:
        pattern = re.compile(r"\ndef\s+logout\s*\(\)\s*:\n(?:    .*\n|\s*\n)+?(?=\ndef\s+\w+\s*\(|\Z)", re.MULTILINE)
        match = pattern.search(text)
        if not match:
            raise RuntimeError("auth_handlers.py içinde değiştirilebilir def logout() bulunamadı.")
        start, end = match.start(), match.end()

    text = text[:start] + "\n\n" + HELPER_BLOCK + "\n\n" + LOGOUT_FUNCTION + "\n" + text[end:]

    if text != original:
        backup(path)
        write_text(path, text)
        return [str(path.relative_to(project_root))]
    return []


def patch_error_handlers(project_root: Path) -> list[str]:
    path = project_root / "app" / "error_handlers.py"
    text = read_text(path)
    original = text

    for marker in ["BYS360_LOGOUT_FORCE_CLEAR_V2_15_12"]:
        text = remove_marker_blocks(text, marker)

    anchor = "\ndef _safe_rollback()"
    idx = text.find(anchor)
    if idx == -1:
        raise RuntimeError("error_handlers.py içinde helper ekleme noktası bulunamadı.")
    text = text[:idx] + "\n\n" + ERROR_HELPER_BLOCK + "\n" + text[idx:]

    old = '''        for key in (\n            "auth.failure_count",\n            "auth.last_failed_at",\n            "login_captcha_question",\n            "login_captcha_answer",\n        ):\n            session.pop(key, None)\n        session.permanent = False\n        session.modified = True\n        flash("Oturum süresi dolduğu için güvenli çıkış tamamlandı. Yeniden giriş yapabilirsiniz.", "info")'''
    new = '''        session.clear()\n        session.permanent = False\n        session.modified = True'''
    if old in text:
        text = text.replace(old, new, 1)
    else:
        text = re.sub(
            r'        for key in \(\n            "auth\.failure_count",\n            "auth\.last_failed_at",\n            "login_captcha_question",\n            "login_captcha_answer",\n        \):\n            session\.pop\(key, None\)\n        session\.permanent = False\n        session\.modified = True\n        flash\([^\n]+\)',
            new,
            text,
            count=1,
        )

    old_return = '''        if _safe_logout_after_expired_csrf():\n            return redirect(url_for("main.login"))'''
    new_return = '''        if _safe_logout_after_expired_csrf():\n            response = redirect(url_for("main.login"))\n            return _bys360_csrf_logout_delete_auth_cookies(response)'''
    if old_return in text:
        text = text.replace(old_return, new_return, 1)
    elif "if _safe_logout_after_expired_csrf():" in text and "_bys360_csrf_logout_delete_auth_cookies" not in text.split("if _safe_logout_after_expired_csrf():", 1)[1][:200]:
        text = text.replace(
            "        if _safe_logout_after_expired_csrf():\n            return redirect(url_for(\"main.login\"))",
            new_return,
            1,
        )

    if text != original:
        backup(path)
        write_text(path, text)
        return [str(path.relative_to(project_root))]
    return []


def patch_routes_no_store(project_root: Path) -> list[str]:
    path = project_root / "app" / "routes.py"
    text = read_text(path)
    original = text

    for marker in [
        "BYS360_LIVE_LOGOUT_FORCE_CLEAR_V2_13_3",
        "BYS360_LIVE_LOGOUT_FORCE_CLEAR_V2_13_4",
        "BYS360_LOGOUT_FORCE_CLEAR_V2_15_12",
    ]:
        text = remove_marker_blocks(text, marker)

    text = re.sub(
        r"\n@main_bp\.after_app_request\s*\ndef\s+bys360_no_store_authenticated_pages\s*\(response\)\s*:\n(?:    .*\n|\s*\n)+?(?=\n@|\ndef\s+|\Z)",
        "\n",
        text,
        flags=re.MULTILINE,
    )
    text = re.sub(
        r"\n@main_bp\.after_app_request\s*\ndef\s+bys360_logout_no_store_authenticated_pages\s*\(response\)\s*:\n(?:    .*\n|\s*\n)+?(?=\n@|\ndef\s+|\Z)",
        "\n",
        text,
        flags=re.MULTILINE,
    )

    candidates = [
        text.find('@main_bp.get("/healthz")'),
        text.find("@main_bp.get('/healthz')"),
        text.find("@main_bp.before_app_request"),
        text.find("@main_bp.route"),
    ]
    candidates = [c for c in candidates if c != -1]
    if not candidates:
        raise RuntimeError("app/routes.py içinde no-store bloğu için yer bulunamadı.")
    insert_at = min(candidates)
    text = text[:insert_at] + NO_STORE_BLOCK + "\n\n" + text[insert_at:]

    if text != original:
        backup(path)
        write_text(path, text)
        return [str(path.relative_to(project_root))]
    return []


def patch_base_template(project_root: Path) -> list[str]:
    path = project_root / "app" / "templates" / "base.html"
    if not path.exists():
        return []
    text = read_text(path)
    original = text
    text = remove_marker_blocks(text, "BYS360_LOGOUT_FORCE_CLEAR_V2_15_12", kind="html")
    match = list(re.finditer(r"</body>", text, flags=re.IGNORECASE))
    if not match:
        return []
    m = match[-1]
    text = text[:m.start()] + "\n" + BASE_LOGOUT_BLOCK + "\n" + text[m.start():]
    if text != original:
        backup(path)
        write_text(path, text)
        return [str(path.relative_to(project_root))]
    return []


def patch_pwa_versions(project_root: Path) -> list[str]:
    patched = []
    for rel in [
        "app/static/pwa/bys360-sw.js",
        "app/static/pwa/service-worker.js",
        "app/static/pwa/sw.js",
        "app/static/pwa/ios-pwa-sw.js",
        "app/static/service-worker.js",
    ]:
        path = project_root / rel
        if not path.exists():
            continue
        text = read_text(path)
        original = text
        text = re.sub(
            r"const\s+BYS360_SW_VERSION\s*=\s*['\"][^'\"]+['\"]\s*;",
            "const BYS360_SW_VERSION = 'bys360-logout-force-clear-v2-15-12';",
            text,
            count=1,
        )
        text = re.sub(
            r"const\s+BYS360_IOS_PWA_CACHE\s*=\s*['\"][^'\"]+['\"]\s*;",
            "const BYS360_IOS_PWA_CACHE = 'bys360-ios-pwa-logout-v2-15-12';",
            text,
            count=1,
        )
        if "bys360-logout-force-clear-v2-15-12" not in text and "bys360-ios-pwa-logout-v2-15-12" not in text:
            text = "// bys360-logout-force-clear-v2-15-12\n" + text
        if "url.pathname.startsWith('/logout')" not in text and 'url.pathname.startsWith("/logout")' not in text:
            inserted = False
            for needle in [
                "if (url.pathname.startsWith('/login')) return true;",
                'if (url.pathname.startsWith("/login")) return true;',
            ]:
                if needle in text:
                    quote = "'" if "'" in needle else '"'
                    text = text.replace(needle, needle + f"\n  if (url.pathname.startsWith({quote}/logout{quote})) return true;", 1)
                    inserted = True
                    break
            if not inserted and "self.addEventListener('fetch'" in text:
                text = text.replace(
                    "self.addEventListener('fetch', event => {",
                    "self.addEventListener('fetch', event => {\n  try { if (new URL(event.request.url).pathname.startsWith('/logout')) return; } catch (e) {}",
                    1,
                )
        if text != original:
            backup(path)
            write_text(path, text)
            patched.append(rel)
    return patched


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    project_root = Path(argv[0]).resolve() if argv else Path.cwd().resolve()
    if not (project_root / "app").exists():
        print(f"Proje kökü bulunamadı: {project_root}")
        return 2

    changed: list[str] = []
    changed += patch_auth_routes(project_root)
    changed += patch_auth_handler(project_root)
    changed += patch_error_handlers(project_root)
    changed += patch_routes_no_store(project_root)
    changed += patch_base_template(project_root)
    changed += patch_pwa_versions(project_root)

    print(f"{VERSION}_APPLY_OK")
    if changed:
        print("Güncellenen dosyalar:")
        for item in changed:
            print(f" - {item}")
    else:
        print("Düzeltmeler zaten uygulanmış görünüyor.")
    print(f"{VERSION}_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
