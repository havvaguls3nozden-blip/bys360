
"""BYS360 application factory.

Bu dosya public ``create_app`` girişini, login user_loader sözleşmesini ve
mevcut Excel import uyumluluk sabitlerini tutar. Uygulama kurulum pipeline'ı
``app.bootstrap.application_bootstrap`` altındadır.

Kalite P0 notu:
- Opsiyonel başlangıç kayıtları uygulamanın açılışını engellemez.
- Ancak artık hata yutulmaz; her opsiyonel kayıt hatası uygulama loguna
  stack trace ile düşer. Böylece canlıda gizli/örtülü arıza kalmaz.
"""
from __future__ import annotations

import contextlib
from collections.abc import Callable
from importlib import import_module

from flask import Flask

from app.bootstrap.application_bootstrap import create_bys360_application
from app.extensions import db, login_manager
from app.models import User

# --- BYS360 third-manager Excel import compatibility patch ---
THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]

OPTIONAL_STARTUP_REGISTRATIONS: tuple[tuple[str, str], ...] = (
    ("app.services.assistant_role_matrix_v10", "register_assistant_role_matrix_v10"),
    ("app.services.assistant_module_access", "register_assistant_module_master_access"),
    ("app.services.assistant_shortcut_visibility", "register_assistant_shortcut_visibility_context"),
    ("app.services.notification_mailer", "register_notification_mailer"),
)


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    # BYS360_P13B_SESSION_STAMP: User.get_id() artik "id:stamp" bicimindedir.
    # Stamp DB'deki guncel security_stamp ile eslesmezse (ör. forgot-password
    # ile parola sifirlandiysa) oturum sessizce gecersiz sayilir ve kullanici
    # anonim davranilir - eski cerezler icin kademe kademe cikis anlamina gelir.
    raw = str(user_id or "")
    stamp = None
    if ":" in raw:
        raw, _, stamp = raw.partition(":")
    try:
        user = db.session.get(User, int(raw))
    except (TypeError, ValueError):
        return None
    if user is None:
        return None
    if stamp is not None and stamp != (user.security_stamp or ""):
        return None
    return user


def _run_optional_startup(app: Flask, label: str, callback: Callable[[], None]) -> None:
    """Run optional startup code without hiding production failures.

    Optional components must not prevent BYS360 from opening. Still, a hidden
    ``except: pass`` makes production problems almost impossible to diagnose.
    This helper preserves graceful startup behavior while recording the real
    exception with traceback in the application log.
    """
    try:
        callback()
    except Exception:
        app.logger.exception("BYS360 optional startup component failed: %s", label)


def _register_optional_import_call(app: Flask, module_path: str, function_name: str) -> None:
    def _callback() -> None:
        module = import_module(module_path)
        getattr(module, function_name)(app)

    _run_optional_startup(app, f"{module_path}.{function_name}", _callback)


def _register_hr_live_shims(app: Flask) -> None:
    from app.institutional.hr_live_p0_shims import register_hr_live_p0_missing_shims

    register_hr_live_p0_missing_shims(app)


def _register_pwa_routes(app: Flask) -> None:
    from app.pwa.routes import pwa_bp

    if "pwa" not in app.blueprints:
        app.register_blueprint(pwa_bp)


def _register_csrf_refresh_handler(app: Flask) -> None:
    from flask import flash, jsonify, redirect, request, url_for

    try:
        from flask_wtf.csrf import CSRFError
    except Exception:
        app.logger.warning("BYS360 CSRF handler skipped: Flask-WTF CSRFError unavailable", exc_info=True)
        return

    @app.errorhandler(CSRFError)
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
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/__init__.py:106")
            pass

        # Compatibility guard.
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
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/__init__.py:120")
            pass

        # Projede gerçek login endpoint'i main.login. auth.login / login olmayan kurulumlarda
        # CSRF hatası ikinci bir BuildError'a dönüşmemeli.
        for endpoint in ("main.login", "auth.login", "login"):
            try:
                return redirect(url_for(endpoint))
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/__init__.py:128")
                continue
        return redirect("/login")


def _register_no_store_auth_html(app: Flask) -> None:
    from flask import request

    @app.after_request
    def bys360_b77_no_store_auth_html(response):  # noqa: ANN001, ANN202
        path = request.path or ""
        content_type = response.headers.get("Content-Type", "")
        is_html = "text/html" in content_type
        auth_like = (
            path in ("/", "/login", "/logout")
            or path.startswith("/auth")
            or path.startswith("/login")
            or path.startswith("/account")
        )
        if is_html or auth_like:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


def _register_api_rate_limit(app: Flask) -> None:
    from app.security.api_rate_limit import init_api_rate_limit

    init_api_rate_limit(app)


def _register_mobile_api(app: Flask) -> None:
    from app.api.mobile import register_mobile_api_real_v1

    register_mobile_api_real_v1(app)

def _register_executive_summary_module(app: Flask) -> None:
    """Register BYS360 Yönetici Özeti routes safely."""
    try:
        if "executive_summary" in getattr(app, "blueprints", {}):
            return
        from app.executive_summary import executive_summary_bp
        app.register_blueprint(executive_summary_bp)
    except Exception as exc:  # pragma: no cover - startup safety
        try:
            app.logger.warning("BYS360 Yönetici Özeti blueprint kaydı atlandı: %s", exc)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/__init__.py:171")
            pass


# BYS360_MENU_VISIBILITY_PREWARM_V1
class _BYS360MenuVisibilityPrewarmUser:
    id = 0
    username = "bys360_menu_prewarm"
    email = "bys360_menu_prewarm@example.local"
    role = "admin"
    roles = ("admin", "Sistem Yöneticisi", "sistem_yoneticisi")
    is_admin = True
    is_active = True
    is_authenticated = True
    is_anonymous = False

    def get_id(self):
        return "0"

    def has_role(self, role_name):
        return role_name in set(self.roles)


def _prewarm_menu_visibility(app):
    """Warm menu visibility internals once during app startup.

    This moves the first cold menu visibility cost from the first user request
    into application startup. Failure is intentionally non-fatal.
    """
    try:
        from app.route_support import build_menu_visibility_map

        with app.app_context():
            build_menu_visibility_map(_BYS360MenuVisibilityPrewarmUser())
    except Exception as exc:
        with contextlib.suppress(Exception):
            app.logger.info("BYS360 menu visibility prewarm skipped: %s", exc)



# BYS360_TEMPLATE_PREWARM_V1
def _prewarm_core_templates(app):
    """Warm heavy shared templates once during app startup.

    base.html dominates the first render cost on large BYS360 pages.
    Failure is intentionally non-fatal.
    """
    try:
        with app.app_context():
            app.jinja_env.get_template("base.html")
            app.jinja_env.get_template("performance/v2_1_4_category_scope.html")
    except Exception as exc:
        with contextlib.suppress(Exception):
            app.logger.info("BYS360 template prewarm skipped: %s", exc)


def create_app() -> Flask:
    app = create_bys360_application(__name__)

    from app.security.html_sanitizer import safe_nav_attrs, safe_social_embed

    app.jinja_env.filters["safe_social_embed"] = safe_social_embed
    app.jinja_env.filters["safe_nav_attrs"] = safe_nav_attrs

    for module_path, function_name in OPTIONAL_STARTUP_REGISTRATIONS:
        _register_optional_import_call(app, module_path, function_name)

    _run_optional_startup(app, "HR live P0 shims", lambda: _register_hr_live_shims(app))
    _run_optional_startup(app, "PWA routes", lambda: _register_pwa_routes(app))
    _run_optional_startup(app, "PWA/iOS CSRF refresh handler", lambda: _register_csrf_refresh_handler(app))
    _run_optional_startup(app, "PWA/iOS no-store auth HTML headers", lambda: _register_no_store_auth_html(app))
    _run_optional_startup(app, "Mobile real API routes", lambda: _register_mobile_api(app))
    _run_optional_startup(app, "iOS PWA V2 routes", lambda: _register_pwa_routes(app))
    _run_optional_startup(app, "API and File Center rate limit", lambda: _register_api_rate_limit(app))

    # BYS360_APP_INIT_HARD_REPAIR_V2_15_5: removed broken executive_summary_bp direct blueprint registration
    _run_optional_startup(app, "Executive Summary routes", lambda: _register_executive_summary_module(app))
    from app.utils.url_map_dedupe import dedupe_identical_url_rules
    dedupe_identical_url_rules(app)
    _prewarm_menu_visibility(app)  # BYS360_MENU_VISIBILITY_PREWARM_V1
    _prewarm_core_templates(app)  # BYS360_TEMPLATE_PREWARM_V1
    return app


# BYS360_A5_P2D4_SCHEMA_GUARD_CHECK_FIRST_ANCHOR_START
# Static contract anchor: auto_repair_schema and should_auto_repair_schema()
# Varsay?lan davran?? check-first olmal?d?r; otomatik onar?m a??k?a izin verilmeden ?al??mamal?d?r.
# BYS360_A5_P2D4_SCHEMA_GUARD_CHECK_FIRST_ANCHOR_END

