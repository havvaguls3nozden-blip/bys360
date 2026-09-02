
"""BYS360 ana blueprint omurgası.

Faz 8 ile bu dosya artık gerçek bir toplayıcı/omurga dosyası oldu: ana
blueprint, sağlık uçları, context processor'lar ve modüler route ailelerinin
kayıt importları burada tutuluyor. Büyük gövdeler ilgili handler modüllerinde.
"""
from __future__ import annotations

from flask import abort, current_app, jsonify, request, send_from_directory
from flask_login import current_user, login_required

from app.config import (
    REMOVED_ROUTE_ENDPOINT_PREFIXES,
    REMOVED_ROUTE_PATH_PREFIXES,
    REMOVED_SCOPE_COMPAT_ENDPOINTS,
    is_removed,
)
from app.main_handlers.account_handlers import (
    account,
    account_change_password,
    account_change_photo,
    account_security_setup,
    settings_page,
)
from app.main_handlers.auth_handlers import forgot_password, login, logout, setup_admin
from app.main_handlers.comparison_handlers import (
    my_performance_comparison,
    team_performance_comparison_history,
)
from app.main_handlers.dashboard_handlers import dashboard, db_check
from app.main_handlers.public_handlers import (
    home as _home_handler,
    index as _index_handler,
    kunye as _kunye_handler,
)
from app.route_registry import main_bp
from app.view_helpers import (
    enforce_first_login_security_flow_redirect,
    get_global_risk_banner_context,
    get_menu_visibility_context,
    get_route_helper_context,
)


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

@main_bp.get("/healthz")
def healthz():
    return jsonify({"status": "ok", "service": "bys360"}), 200


@main_bp.get("/readyz")
def readyz():
    schema_errors = list(current_app.extensions.get("schema_check_errors", []) or [])
    payload = {
        "status": "ready" if not schema_errors else "degraded",
        "service": "bys360",
        "app_env": current_app.config.get("APP_ENV", "development"),
        "schema_error_count": len(schema_errors),
    }
    return jsonify(payload), (200 if not schema_errors else 503)

# BYS360_PROFILE_PHOTO_VISIBILITY_V2_17_73_BEGIN
@main_bp.get("/uploads/profile_photos/<path:filename>")
@login_required
def bys360_profile_photo_file(filename: str):
    """Profil fotoğraflarını kırık görsel oluşturmadan güvenli biçimde sunar."""
    import os
    from pathlib import Path

    from werkzeug.utils import secure_filename

    safe_name = secure_filename(Path(filename or "").name)
    if not safe_name:
        abort(404)

    roots = []
    static_profile_dir = (Path(current_app.root_path) / "static" / "uploads" / "profile_photos").resolve()
    roots.append(static_profile_dir)

    configured_upload_root = current_app.config.get("UPLOAD_FOLDER") or os.getenv("UPLOAD_FOLDER")
    if configured_upload_root:
        upload_root = Path(str(configured_upload_root)).resolve()
        roots.append((upload_root / "profile_photos").resolve())
        roots.append((upload_root / "uploads" / "profile_photos").resolve())

    for root in roots:
        candidate = (root / safe_name).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if candidate.is_file():
            response = send_from_directory(str(root), safe_name, as_attachment=False, conditional=True)
            response.headers.setdefault("Cache-Control", "private, max-age=3600")
            return response

    default_dir = (Path(current_app.root_path) / "static" / "img").resolve()
    response = send_from_directory(str(default_dir), "default-avatar.svg", as_attachment=False, conditional=True)
    response.headers.setdefault("Cache-Control", "private, max-age=600")
    return response
# BYS360_PROFILE_PHOTO_VISIBILITY_V2_17_73_END


def _bys360_release_identity() -> dict[str, str | None]:
    """BYS360 DEFECT Z: reads THIS running process's own bundled
    CANDIDATE_READY.json (written by prepare_bys360_candidate.ps1, verified
    and carried across promotion by cutover_bys360_candidate.ps1) to expose
    the release this specific process was actually promoted from. Every
    promoted version lives at the same fixed C:\\bys360\\project path, so
    process/PID/path metadata alone can never distinguish WHICH release's
    code is currently loaded -- this is the one place that can. Absent in
    local/dev environments not managed by that pipeline; never raises."""
    import json
    from pathlib import Path

    receipt_path = Path(current_app.root_path).parent / "CANDIDATE_READY.json"
    try:
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception:
        return {"source_sha": None, "migration_head": None}
    return {
        "source_sha": data.get("SOURCE_SHA"),
        "migration_head": data.get("MIGRATION_HEAD"),
    }


@main_bp.get("/versionz")
def versionz():
    runtime_manifest = current_app.extensions.get("runtime_route_manifest") or {}
    schema_errors = list(current_app.extensions.get("schema_check_errors", []) or [])
    release = _bys360_release_identity()
    return jsonify({
        "service": "bys360",
        "app_env": current_app.config.get("APP_ENV", "development"),
        "route_count": len(runtime_manifest) if isinstance(runtime_manifest, dict) else 0,
        "schema_error_count": len(schema_errors),
        "source_sha": release["source_sha"],
        "migration_head": release["migration_head"],
    }), 200


@main_bp.before_app_request
def block_removed_module_routes():
    endpoint = str(getattr(request, "endpoint", "") or "")
    path = str(getattr(request, "path", "") or "")

    if endpoint in REMOVED_SCOPE_COMPAT_ENDPOINTS:
        return None

    for module_name, prefixes in REMOVED_ROUTE_ENDPOINT_PREFIXES.items():
        if not is_removed(module_name):
            continue
        for prefix in prefixes:
            if endpoint == prefix or endpoint.startswith(prefix):
                abort(404)

    for module_name, prefixes in REMOVED_ROUTE_PATH_PREFIXES.items():
        if not is_removed(module_name):
            continue
        for prefix in prefixes:
            if path == prefix or path.startswith(prefix + "/"):
                abort(404)


@main_bp.app_context_processor
def inject_menu_visibility():
    return get_menu_visibility_context()


@main_bp.app_context_processor
def inject_global_risk_banner():
    return get_global_risk_banner_context()


@main_bp.app_context_processor
def inject_route_helpers():
    return get_route_helper_context()


def enforce_first_login_security_flow():
    return enforce_first_login_security_flow_redirect()


main = main_bp  # BYS360_PHASE10_MAIN_BLUEPRINT_ALIAS
@main_bp.route("/")
def index():
    return _index_handler()


@main_bp.route("/home")
@login_required
def home():
    return _home_handler()


# Modüler ana blueprint route aileleri
from app.account import routes as _account_routes  # noqa: E402,F401
from app.admin import routes as _admin_routes  # noqa: E402,F401
from app.ai import routes as _ai_routes  # noqa: E402,F401
from app.auth import routes as _auth_routes  # noqa: E402,F401
from app.communication import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    feedback_routes as _feedback_routes,  # noqa: E402,F401
    routes as _communication_routes,  # noqa: E402,F401
    user_feedback_routes as _bys360_user_feedback_routes,  # noqa: E402,F401
)
from app.dashboard import routes as _dashboard_routes  # noqa: E402,F401
from app.institutional import routes as _institutional_routes  # noqa: E402,F401
from app.performance import routes as _performance_routes  # noqa: E402,F401

# BYS360_CORPORATE_PORTAL_V1_ROUTE_IMPORT
from app.portal import routes as _portal_routes  # noqa: E402,F401
from app.support import routes as _support_routes  # noqa: E402,F401

__all__ = [
    "main_bp",
    "healthz",
    "readyz",
    "versionz",
    "index",
    "home",
    "login",
    "forgot_password",
    "logout",
    "setup_admin",
    "dashboard",
    "settings_page",
    "account",
    "account_change_photo",
    "account_security_setup",
    "account_change_password",
    "db_check",
    "my_performance_comparison",
    "team_performance_comparison_history",
]

@main_bp.route("/kunye")
def kunye():
    return _kunye_handler()

# BYS360_PHASE10_REPORTS_ROUTE_IMPORT_AFTER_MAIN
try:
    from app.performance import (
        process_engine_phase10_reports_routes as _phase10_reports_routes,  # noqa: F401,E402
    )
except ImportError:  # route import should never break app startup silently
    raise

# BYS360_PHASE12_PRESIDENT_APPROVALS_CARD_ROUTE_IMPORT
try:
    from app.performance import (
        president_low_score_card_routes as _bys360_phase12_president_card_routes,  # noqa: F401,E402
    )
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/routes.py)")
# /BYS360_PHASE12_PRESIDENT_APPROVALS_CARD_ROUTE_IMPORT

# BYS360_SP2F_STRATEGIC_PERFORMANCE_SIDEBAR_ROUTE_IMPORT
try:
    from app.performance import sp1_sidebar_routes as _sp2f_sp1_sidebar_routes  # noqa: F401,E402
except Exception:
    # Route uyumluluğu uygulama açılışını bozmasın; gate scripti ayrıca doğrular.
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/routes.py:184)")
# /BYS360_SP2F_STRATEGIC_PERFORMANCE_SIDEBAR_ROUTE_IMPORT

# BYS360_MOBILE_PWA_FAZ2_V1_ROUTES_BEGIN
@main_bp.get("/manifest.webmanifest")
def bys360_pwa_manifest():
    from flask import current_app, make_response, send_from_directory
    assert current_app.static_folder is not None, "BYS360 app must have a configured static folder"
    response = make_response(send_from_directory(current_app.static_folder, "pwa/manifest.webmanifest", mimetype="application/manifest+json"))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@main_bp.get("/bys360-sw.js")
def bys360_pwa_service_worker():
    from flask import current_app, make_response, send_from_directory
    assert current_app.static_folder is not None, "BYS360 app must have a configured static folder"
    response = make_response(send_from_directory(current_app.static_folder, "pwa/bys360-sw.js", mimetype="application/javascript"))
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
# BYS360_MOBILE_PWA_FAZ2_V1_ROUTES_END


# BYS360 V2 route bootstrap tarafindan yukleniyor; app.routes importu kapatildi

# BYS360_CORPORATE_INFORMATION_CENTER_V3_ROUTE_IMPORT
try:
    from app.communication import (
        corporate_information_center_routes as _bys360_corporate_information_center_routes,  # noqa: F401,E402
    )
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 Kurumsal Bilgilendirme Merkezi route import failed")
# /BYS360_CORPORATE_INFORMATION_CENTER_V3_ROUTE_IMPORT


# BYS360_A5_P2D4_LIVE_SCOPE_PORTAL_PREFIX_ANCHOR_START
# Static contract anchor: /portal
# Portal prefix canl? kapsam/karantina s?zle?mesinde a??k?a izlenir.
# BYS360_A5_P2D4_LIVE_SCOPE_PORTAL_PREFIX_ANCHOR_END
# BYS360 Dosya Merkezi route kayıtları
# Bu import, app/file_center/routes.py içindeki main_bp route dekoratörlerini uygulamaya bağlar.
from app.file_center import routes as _file_center_routes  # noqa: F401,E402

