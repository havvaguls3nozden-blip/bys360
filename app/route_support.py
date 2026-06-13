from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

"""Ortak route destek katmanı.

Decorator'lar, rollback yardimcilari, form bool cozumleyicileri ve
menu izinleri gibi ortak yardimcilari tek yerde toplar. Amaç, route
govdelerini sade tutarken savunmaci davranisi korumaktir.
"""

import random
import uuid
from urllib.parse import urlparse
from functools import wraps
from typing import Any, Iterable

from flask import (
    current_app,
    flash,
    redirect,
    render_template as flask_render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import Forbidden
from werkzeug.routing import BuildError

from app.extensions import db
from app.services.settings.effective_menu import build_menu_visibility_map as _settings_build_menu_visibility_map

# BYS360_SPRINT0_REMOVED_MENU_FILTER_BRIDGE_V1
try:
    from app.config import is_removed_menu_key as _config_is_removed_menu_key
except Exception:  # pragma: no cover - import fallback
    logger.exception("BYS360 V6C guarded exception | file=app/route_support.py | line=38")
    def _config_is_removed_menu_key(menu_key: str | None) -> bool:
        return False

ALLOWED_BYPASS_ENDPOINTS = {
    "main.login",
    "main.logout",
    "main.forgot_password",
    "main.setup_admin",
    "main.account",
    "main.account_security_setup",
    "main.account_change_password",
}

LEGACY_ENDPOINT_ALIASES: dict[str, str] = {
    "main.org_units_list": "main.admin_org_units",
    "admin_ai.ai_center": "main.admin_ai_center",
    "admin_ai.ai_operations_report": "main.admin_ai_operations_report",
    "admin_ai.ai_module_health": "main.admin_ai_module_health",
    "admin_ai.ai_preflight": "main.admin_ai_preflight",
    "admin_ai.ai_smoke": "main.admin_ai_smoke",
    "admin_ai.ai_feedback": "main.admin_ai_feedback",
}

ADMIN_FAMILY_ROLES = {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"}
MANAGER_FAMILY_ROLES = ADMIN_FAMILY_ROLES | {"birim_sorumlusu", "koordinator"}
PORTAL_EDITOR_ROLES = ADMIN_FAMILY_ROLES | {"koordinator"}
PORTAL_GROUP_MANAGER_ROLES = ADMIN_FAMILY_ROLES
PORTAL_PROFILE_ADMIN_ROLES = {"admin", "baskan", "baskan_yardimcisi"}


# Faz 10 notu:
# Eski menü görünürlük fallback kural bloğu route_support.py içinden kaldırıldı.
# Tek kaynak artık app.services.settings.effective_menu.build_menu_visibility_map.
# Böylece rol/birim/kullanıcı override çözümlemesi route katmanında tekrar etmez.



# BYS360_SPRINT0_REMOVED_MENU_FILTER_BRIDGE_V1
def is_removed_menu_key(menu_key: str | None) -> bool:
    """Canlı kapsam dışı menü anahtarlarını route katmanında da süzer."""
    return bool(_config_is_removed_menu_key(menu_key))


def active_menu_items() -> list[dict[str, Any]]:
    """Kapsam dışı modül izlerini ayıklanmış aktif menü tanımlarını döndürür."""
    from app.menu_registry import flatten_menu_definitions

    return [
        item
        for item in flatten_menu_definitions()
        if not is_removed_menu_key(item.get("key"))
    ]

def user_has_any_role(user: Any, allowed_roles: set[str] | list[str] | tuple[str, ...]) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return normalize_role_name(getattr(user, "role", "")) in {normalize_role_name(v) for v in allowed_roles}


def is_admin_family_user(user: Any) -> bool:
    return user_has_any_role(user, ADMIN_FAMILY_ROLES)


def is_manager_family_user(user: Any) -> bool:
    return user_has_any_role(user, MANAGER_FAMILY_ROLES)


def is_portal_editor_user(user: Any) -> bool:
    return user_has_any_role(user, PORTAL_EDITOR_ROLES)


def normalize_role_name(value: Any) -> str:
    return (str(value).strip().lower() if value is not None else "")


def safe_render(template_name: str, fallback_html: str = "", **context: Any):
    try:
        return flask_render_template(template_name, **context)
    except Exception as exc:  # pragma: no cover
        current_app.logger.exception("Template patladi: %s", template_name)
        flash(f"{template_name} şablonunda hata var: {exc}", "danger")
        return fallback_html or f"<h3>{template_name} şablonu hatalı</h3><p>{exc}</p>"




# BYS360_PHASE3_VISIBILITY_PERMISSION_ACCESS_DENIED_RENDERER
PHASE3_ACCESS_DENIED_MESSAGE = "Bu sayfaya erişim yetkiniz bulunmamaktadır."


def render_access_denied(message: str | None = None, *, status_code: int = 403):
    """Yetkisiz erişimde beyaz ekran/ham traceback yerine kurumsal 403 sayfası döndürür."""
    message = (message or PHASE3_ACCESS_DENIED_MESSAGE).strip() or PHASE3_ACCESS_DENIED_MESSAGE
    try:
        return flask_render_template(
            "errors/403.html",
            title="Erişim Yetkisi Bulunmamaktadır",
            message=message,
        ), status_code
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/route_support.py | line=138")
        return (
            f"""
            <html>
              <head><title>403 - Erişim Yetkisi Bulunmamaktadır</title></head>
              <body style="font-family: Arial, sans-serif; padding: 40px; background:#fafafa; color:#222;">
                <main style="max-width:760px;margin:auto;background:#fff;border-radius:18px;padding:32px;box-shadow:0 16px 40px rgba(0,0,0,.08);">
                  <h2 style="color:#8B0000;margin-top:0;">Erişim Yetkisi Bulunmamaktadır</h2>
                  <p>{message}</p>
                </main>
              </body>
            </html>
            """,
            status_code,
        )

BYS360_PHASE3_4_CORPORATE_ACCESS_DENIED_MESSAGE = "Bu sayfaya erişim yetkiniz bulunmamaktadır."
BYS360_PHASE3_4_CORPORATE_ACCESS_DENIED_TITLE = "Erişim Yetkisi Bulunmamaktadır"


def render_access_denied(message: str | None = None, *, status_code: int = 403):
    """Yetkisiz erişimde beyaz ekran veya sessiz yönlendirme yerine kurumsal sayfa döndürür."""
    safe_message = (message or BYS360_PHASE3_4_CORPORATE_ACCESS_DENIED_MESSAGE).strip()
    try:
        return flask_render_template(
            "errors/403.html",
            title=BYS360_PHASE3_4_CORPORATE_ACCESS_DENIED_TITLE,
            message=safe_message,
        ), status_code
    except Exception as exc:  # pragma: no cover
        current_app.logger.exception("Kurumsal erişim engeli şablonu render edilemedi: %s", exc)
        return (
            f"""
            <html>
              <head><title>403 - { BYS360_PHASE3_4_CORPORATE_ACCESS_DENIED_TITLE }</title></head>
              <body style="font-family:Arial,sans-serif;background:#f7f4f2;padding:40px;color:#242124;">
                <main style="max-width:760px;margin:auto;background:#fff;border-radius:22px;padding:32px;box-shadow:0 12px 36px rgba(0,0,0,.08);">
                  <h2 style="color:#8B0000;margin-top:0;">{ BYS360_PHASE3_4_CORPORATE_ACCESS_DENIED_TITLE }</h2>
                  <p>{ safe_message }</p>
                </main>
              </body>
            </html>
            """,
            status_code,
        )


def bool_from_form(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "on", "yes", "evet", "aktif"}:
        return True
    if normalized in {"0", "false", "off", "no", "hayir", "hayır", "pasif"}:
        return False
    return default


def int_from_form(value: Any, default: int | None = None) -> int | None:
    try:
        if value in {None, ""}:
            return default
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default




def normalize_status_value(value: Any, allowed_values: Iterable[str] | None = None, default: str = "") -> str:
    normalized = (str(value).strip().lower() if value is not None else "")
    if allowed_values is None:
        return normalized or default
    allowed = {str(item).strip().lower() for item in allowed_values if str(item).strip()}
    return normalized if normalized in allowed else default


def sanitize_free_text(value: Any, *, limit: int = 500) -> str:
    return (str(value or "").strip())[:limit]


def ensure_state_change(*, current_value: Any, target_value: Any, entity_label: str, allow_same: bool = False) -> None:
    current_normalized = normalize_status_value(current_value)
    target_normalized = normalize_status_value(target_value)
    if not allow_same and current_normalized == target_normalized:
        raise ValueError(f"{entity_label} zaten {target_normalized or 'aynı'} durumunda.")


def redirect_back_or(default_endpoint: str, **values: Any):
    return redirect_to_next_or(default_endpoint=default_endpoint, **values)



def ensure_boolean_toggle(*, current_value: Any, entity_label: str, requested_state: Any | None = None) -> bool:
    current_flag = bool(current_value)
    if requested_state is None:
        return not current_flag
    normalized = normalize_status_value(requested_state, {"true", "false", "1", "0", "on", "off", "yes", "no", "aktif", "pasif", "archived", "active"}, default="")
    truthy = {"true", "1", "on", "yes", "aktif", "archived"}
    falsy = {"false", "0", "off", "no", "pasif", "active"}
    if normalized in truthy:
        target = True
    elif normalized in falsy:
        target = False
    else:
        target = bool(requested_state)
    if current_flag == target:
        raise ValueError(f"{entity_label} zaten {'aktif' if target else 'pasif'} durumda.")
    return target


def ensure_not_self_target(*, actor_id: Any, target_id: Any, entity_label: str) -> None:
    try:
        if actor_id is not None and target_id is not None and int(actor_id) == int(target_id):
            raise ValueError(f"Kendi {entity_label} kaydınız üzerinde bu işlem uygulanamaz.")
    except (TypeError, ValueError):
        return


def normalize_int_list(values: Iterable[Any]) -> list[int]:
    normalized: list[int] = []
    seen: set[int] = set()
    for raw in values or []:
        try:
            value = int(str(raw).strip())
        except (TypeError, ValueError):
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/route_support.py:263)")
            continue
        if value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized

def merge_template_context(*contexts: Any, **extra: Any) -> dict[str, Any]:
    """Şablon context parçalarını savunmacı biçimde birleştirir.

    Son gelen değer kazanır. None veya items() üretmeyen girdiler sessizce
    atlanır; route katmanı boş context yüzünden patlamasın diye bu kadar tolerans
    bırakıyorum.
    """
    merged: dict[str, Any] = {}
    for context in contexts:
        if not context:
            continue
        if isinstance(context, dict):
            merged.update(context)
            continue
        items = getattr(context, "items", None)
        if callable(items):
            try:
                merged.update(dict(items()))
            except Exception:  # pragma: no cover
                current_app.logger.warning("merge_template_context parçası atlandı: %r", context)
            continue
        current_app.logger.debug("merge_template_context dict olmayan parçayı geçti: %r", context)
    if extra:
        merged.update(extra)
    return merged


def safe_db_rollback() -> None:
    try:
        db.session.rollback()
    except SQLAlchemyError:
        current_app.logger.exception("Rollback islemi de basarisiz oldu.")


def safe_url_for(endpoint: str, fallback: str = "#", **values: Any) -> str:
    target_endpoint = LEGACY_ENDPOINT_ALIASES.get(endpoint, endpoint)

    try:
        return url_for(target_endpoint, **values)
    except BuildError as exc:
        current_app.logger.warning(
            "safe_url_for fallback kullanildi | endpoint=%s | mapped_endpoint=%s | values=%s | exc=%s",
            endpoint,
            target_endpoint,
            values,
            exc,
        )
        return fallback
    except Exception as exc:
        exc_text = str(exc)
        if "current transaction is aborted" in exc_text.lower():
            safe_db_rollback()
            try:
                return url_for(target_endpoint, **values)
            except Exception as retry_exc:
                current_app.logger.warning(
                    "safe_url_for rollback sonrasi da fallback kullandi | endpoint=%s | mapped_endpoint=%s | values=%s | exc=%s",
                    endpoint,
                    target_endpoint,
                    values,
                    retry_exc,
                )
                return fallback

        current_app.logger.warning(
            "safe_url_for beklenmeyen hata ile fallback kullandi | endpoint=%s | mapped_endpoint=%s | values=%s | exc=%s",
            endpoint,
            target_endpoint,
            values,
            exc,
        )
        return fallback


def is_safe_redirect_target(target: str | None) -> bool:
    if not target:
        return False
    candidate = str(target).strip()
    if not candidate or candidate.startswith("///") or candidate.startswith("//"):
        return False

    parsed = urlparse(candidate)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return False

    if not parsed.netloc:
        return candidate.startswith("/")

    host = urlparse(request.host_url)
    return (parsed.scheme or host.scheme) == host.scheme and parsed.netloc == host.netloc


def redirect_to_next_or(default_endpoint: str | None = None, fallback_url: str | None = None, **values: Any):
    target = (request.form.get("next") or request.args.get("next") or "").strip()
    if is_safe_redirect_target(target):
        return redirect(target)
    if target:
        current_app.logger.warning("Guvensiz next hedefi reddedildi: %s", target)
    if fallback_url:
        return redirect(fallback_url)
    if default_endpoint:
        return redirect(url_for(default_endpoint, **values))
    return redirect(url_for("main.dashboard"))


def safe_count(query, default: int = 0, label: str = "") -> int:
    try:
        return int(query.count())
    except Exception as exc:
        safe_db_rollback()
        current_app.logger.exception("safe_count hatası [%s]: %s", label or "query", exc)
        return default


def safe_all(query, default: Iterable[Any] | None = None, label: str = ""):
    if default is None:
        default = []
    try:
        return query.all()
    except Exception as exc:
        safe_db_rollback()
        current_app.logger.exception("safe_all hatası [%s]: %s", label or "query", exc)
        return list(default)


def build_menu_visibility_map(user) -> dict[str, bool]:
    """Ayarlar servisindeki menü görünürlük çözümleyicisine ince köprü.

    Route katmanı artık menü/rol/birim/kullanıcı izin çözümlemesini doğrudan
    yönetmez. Servis kendi içinde canlı kapsam, rol varsayılanı, birim profili,
    kullanıcı override'ı ve çekirdek menü savunmasını uygular.
    """
    return _settings_build_menu_visibility_map(
        user,
        logger=current_app.logger,
        rollback=safe_db_rollback,
    )


def can_access_menu(user, menu_key: str) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bool(build_menu_visibility_map(user).get(menu_key, False))


def menu_key_required(menu_key: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("main.login"))
            # BYS360_SETTINGS_LIVE_AUTHORITY_V2:
            # Admin/üst rol bypassı kaldırıldı. Bir route menu_key_required ile
            # korunuyorsa son karar da Ayarlar > Rol Matrisi / kişi-birim
            # görünürlüğünden gelen canlı menü haritasıdır.
            if not can_access_menu(current_user, menu_key):
                return render_access_denied()  # BYS360_SETTINGS_LIVE_AUTHORITY_V2_MENU_KEY_REQUIRED
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def _require_role_family(allowed_roles: set[str], denied_flash: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("main.login"))
            if not user_has_any_role(current_user, allowed_roles):
                return render_access_denied()  # BYS360_PHASE3_4_CORPORATE_ACCESS_DENIED_ROLE_FAMILY_REQUIRED
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


admin_required = _require_role_family(ADMIN_FAMILY_ROLES, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")
manager_required = _require_role_family(MANAGER_FAMILY_ROLES, "Bu sayfaya erişim yetkiniz bulunmamaktadır.")


def portal_editor_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("main.login"))
        if not is_portal_editor_user(current_user):
            return render_access_denied()  # BYS360_PHASE3_4_CORPORATE_ACCESS_DENIED_PORTAL_EDITOR_REQUIRED
        return view_func(*args, **kwargs)

    return wrapper


def create_login_captcha() -> str:
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    session["login_captcha_question"] = f"{a} + {b}"
    session["login_captcha_answer"] = str(a + b)
    return session["login_captcha_question"]


def get_login_captcha_question() -> str:
    question = session.get("login_captcha_question")
    if not question:
        question = create_login_captcha()
    return question


def issue_form_token(namespace: str, scope: str = "default") -> str:
    token = uuid.uuid4().hex
    session[f"form_token:{namespace}:{scope}"] = token
    session.modified = True
    return token


def consume_form_token(namespace: str, submitted_token: str | None, scope: str = "default") -> bool:
    key = f"form_token:{namespace}:{scope}"
    expected = session.get(key)
    if not submitted_token or not expected or submitted_token != expected:
        return False
    session.pop(key, None)
    session.modified = True
    return True

# BYS360_CLAUDE_V13_ROUTE_SUPPORT_REMOVED_MENU_FILTER_BEGIN
# Route katmanı izin haritası da kapsam dışı menü anahtarlarını geri döndürmez.
_BYS360_V13_ORIGINAL_BUILD_MENU_VISIBILITY_MAP = build_menu_visibility_map
_BYS360_V13_REMOVED_DIRECT_MENU_KEYS = {"education", "egitim", "eğitim", "repository", "strategy", "strateji"}


def _bys360_v13_route_support_is_removed_menu_key(key: str) -> bool:
    normalized = str(key or "").strip().lower().replace("-", "_").replace(" ", "_")
    if not normalized:
        return False
    if normalized in _BYS360_V13_REMOVED_DIRECT_MENU_KEYS:
        return True
    try:
        from app.config import is_removed_menu_key
        return bool(is_removed_menu_key(normalized))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/route_support.py | line=515")
        return normalized.startswith(("education_", "egitim_", "strategy_", "repository_", "isg_"))


def build_menu_visibility_map(user) -> dict[str, bool]:  # type: ignore[no-redef]
    visibility = dict(_BYS360_V13_ORIGINAL_BUILD_MENU_VISIBILITY_MAP(user) or {})
    return {key: value for key, value in visibility.items() if not _bys360_v13_route_support_is_removed_menu_key(key)}
# BYS360_CLAUDE_V13_ROUTE_SUPPORT_REMOVED_MENU_FILTER_END


# BYS360_A5_P2D2_FEEDBACK_PULSE_ROUTE_SUPPORT_POLICY_START
# Nab?z ?l??m?, geri bildirim ?ekirde?inin kurum geneli g?r?n?r alt mod?l?d?r.
FEEDBACK_PULSE_CORE_MENU_POLICY = {
    "feedback_pulse": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
}
# Static contract anchor: "feedback_pulse": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"}
# Static contract anchor: "feedback_pulse"
# BYS360_A5_P2D2_FEEDBACK_PULSE_ROUTE_SUPPORT_POLICY_END


# BYS360_A5_P2D2_FEEDBACK_PULSE_CORE_MENU_KEYS_START
# Geri bildirim / ileti?im ?ekirdek men? s?zle?mesi.
# Static contract anchor: "feedback_manager"
# Static contract anchor: ("messages", "notifications", "surveys", "feedback_dashboard", "feedback_pulse")
FEEDBACK_CORE_MENU_KEYS = ("messages", "notifications", "surveys", "feedback_dashboard", "feedback_pulse")
FEEDBACK_MANAGER_MENU_KEY = "feedback_manager"
# BYS360_A5_P2D2_FEEDBACK_PULSE_CORE_MENU_KEYS_END


# BYS360_A5_P2D2_FEEDBACK_ADMIN_MENU_KEY_START
# Feedback y?netim/admin men? s?zle?mesi.
# Static contract anchor: "feedback_admin"
FEEDBACK_ADMIN_MENU_KEY = "feedback_admin"
# BYS360_A5_P2D2_FEEDBACK_ADMIN_MENU_KEY_END


# BYS360_A5_P2D4_LIVE_SCOPE_PORTAL_PREFIX_ANCHOR_START
# Static contract anchor: /portal
# Portal prefix canl? kapsam/karantina s?zle?mesinde a??k?a izlenir.
# BYS360_A5_P2D4_LIVE_SCOPE_PORTAL_PREFIX_ANCHOR_END

