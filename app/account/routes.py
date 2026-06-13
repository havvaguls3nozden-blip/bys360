
"""Phase 43 modular account, settings and security flow route family."""
from __future__ import annotations

from flask import current_app, render_template_string
from flask_login import login_required

from app.main_handlers import account_handlers as _handlers
from app.route_registry import main_bp
from app.route_support import admin_required

LEGACY_SHIM = False
LEGACY_RUNTIME_STATUS = "active_modular_main_blueprint_routes"
LEGACY_ROUTE_FAMILY = "account_settings_security_flow"
LEGACY_NOTE = (
    "Phase 43 ile hesap, ayarlar ve ilk giriş güvenlik akışı route kayıtları "
    "modüler yapıya taşındı. Gövde implementasyonları uyumluluk için "
    "app.routes içinde helper olarak korunur."
)


@main_bp.before_app_request
def enforce_first_login_security_flow():
    return _handlers.enforce_first_login_security_flow()


@main_bp.route("/settings", methods=["GET", "POST"])
@login_required
@admin_required
def settings_page():
    try:
        return _handlers.settings_page()
    except Exception as exc:  # BYS360_V58_SETTINGS_SAFE_FALLBACK
        current_app.logger.exception("Ayarlar sayfası güvenli fallback ile açıldı: %s", exc)
        return render_template_string(
            """
            <html lang="tr">
              <head>
                <meta charset="utf-8">
                <title>Ayarlar</title>
                <style>
                  body{margin:0;background:#f6f2ef;font-family:Arial,sans-serif;color:#2b2424;}
                  main{max-width:880px;margin:48px auto;background:#fff;border-radius:22px;padding:30px;box-shadow:0 16px 42px rgba(0,0,0,.08);border-left:8px solid #8B0000;}
                  h1{margin:0 0 12px;color:#8B0000;font-size:24px;}
                  p{line-height:1.65;font-size:15px;}
                  .muted{color:#6b6060;font-size:13px;}
                </style>
              </head>
              <body>
                <main>
                  <h1>Ayarlar sayfası güvenli modda açıldı</h1>
                  <p>Ayarlar omurgası canlı sistemi durdurmadan korunuyor. Sayfa verileri hazırlanırken bir uyumsuzluk algılandı; sistem hata ekranı yerine güvenli bilgilendirme gösterdi.</p>
                  <p class="muted">Lütfen v58 gate kontrolünü ve veritabanı migration adımını çalıştırın.</p>
                </main>
              </body>
            </html>
            """
        ), 200


@main_bp.route("/account")
@login_required
def account():
    return _handlers.account()


@main_bp.route("/account/photo", methods=["POST"])
@login_required
def account_change_photo():
    return _handlers.account_change_photo()


@main_bp.route("/account/security-setup", methods=["GET", "POST"])
@login_required
def account_security_setup():
    return _handlers.account_security_setup()


@main_bp.route("/account/change-password", methods=["GET", "POST"])
@login_required
def account_change_password():
    return _handlers.account_change_password()