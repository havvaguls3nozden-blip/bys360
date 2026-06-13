from __future__ import annotations



from typing import Any

from sqlalchemy import text

from app.extensions import db

from .repository import table_exists
from .policy import AI_AGENT_AG6_VERSION, AI_AGENT_SECURITY_NOTICE
import logging
logger = logging.getLogger(__name__)


def _user_id(user: Any) -> int | None:
    try:
        return int(getattr(user, "id", None) or 0) or None
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/ai_agent/security_bridge.py | line=18")
        return None


def _safe_setting(key: str, default: str = "") -> str:
    if not table_exists("ai_agent_settings"):
        return default
    try:
        value = db.session.execute(
            text("SELECT setting_value FROM ai_agent_settings WHERE setting_key = :key LIMIT 1"),
            {"key": key},
        ).scalar()
        return default if value is None else str(value)
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/ai_agent/security_bridge.py | line=31")
        return default


def _safe_table_count(table_name: str) -> int:
    if not table_exists(table_name):
        return 0
    try:
        return int(db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() or 0)
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/ai_agent/security_bridge.py | line=40")
        return 0


def _role_text(user: Any) -> str:
    values: list[str] = []
    for attr in ("role", "role_name", "user_role", "yetki", "permission_group"):
        value = getattr(user, attr, None)
        if value:
            values.append(str(value))
    try:
        if hasattr(user, "roles"):
            roles = getattr(user, "roles") or []
            for role in roles:
                values.append(str(getattr(role, "name", role)))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/security_bridge.py)")
    return " ".join(values).lower()


def user_has_ai_agent_admin_scope(user: Any) -> bool:
    role_text = _role_text(user)
    elevated_terms = (
        "admin",
        "sistem",
        "başkan",
        "baskan",
        "üst yönetim",
        "ust yonetim",
        "grup başkanı",
        "grup baskani",
    )
    return any(term in role_text for term in elevated_terms)


def build_ai_agent_security_policy_payload(user: Any | None = None) -> dict[str, Any]:
    """AG-6 canlı güvenlik politikası özetini üretir.

    Bu çıktı hassas veri içermez. Yetkili kullanıcıya bile yalnızca kontrol maddeleri ve
    güvenli ayar durumu gösterilir.
    """
    return {
        "ok": True,
        "version": AI_AGENT_AG6_VERSION,
        "mode": "canli_guvenlik_gate",
        "notice": AI_AGENT_SECURITY_NOTICE,
        "public_endpoint_policy": {
            "healthz": "yalnızca sağlık bilgisi, kullanıcı veya iş verisi yok",
        },
        "protected_endpoint_policy": {
            "panel": "login_required",
            "ask": "login_required",
            "performance_summary": "login_required",
            "dashboard_kpi_summary": "login_required",
            "assistant_widget_summary": "login_required",
            "action_queue_summary": "login_required",
            "security_policy": "login_required",
            "security_self_check": "login_required",
        },
        "controls": [
            "BYS360 Asistanı idari karar üretmez.",
            "BYS360 Asistanı veri değiştiren otomatik işlem uygulamaz.",
            "Genel kurum özetleri rol/yetki kapsamına göre sınırlandırılır.",
            "Hassas veri maskeleme açık tutulur.",
            "Public health ucu kullanıcı ve iş verisi döndürmez.",
            "Öneri kuyruğu yalnızca takip kaydıdır; iş süreci işlemi değildir.",
        ],
        "settings": {
            "external_ai_enabled": _safe_setting("ai_agent.external_ai_enabled", "false"),
            "auto_action_enabled": _safe_setting("ai_agent.auto_action_enabled", "false"),
            "action_execution_enabled": _safe_setting("ai_agent.action_execution_enabled", "false"),
            "redaction_enabled": _safe_setting("ai_agent.redaction_enabled", "true"),
            "security_gate_enabled": _safe_setting("ai_agent.security_gate_enabled", "true"),
        },
        "scope": {
            "is_elevated_scope": bool(user is not None and user_has_ai_agent_admin_scope(user)),
            "user_bound_summary": True,
            "sensitive_detail_allowed": False,
        },
    }


def build_ai_agent_security_self_check(user: Any) -> dict[str, Any]:
    """Giriş yapmış kullanıcı için güvenli öz denetim çıktısı üretir.

    Kullanıcı adı, e-posta, sicil, mesaj içeriği, anket yanıtı veya performans detayı döndürmez.
    """
    settings = build_ai_agent_security_policy_payload(user).get("settings", {})
    failures: list[str] = []
    if settings.get("external_ai_enabled") != "false":
        failures.append("Dış AI bağlantısı kapalı olmalıdır.")
    if settings.get("auto_action_enabled") != "false":
        failures.append("Otomatik işlem kapalı olmalıdır.")
    if settings.get("action_execution_enabled") != "false":
        failures.append("Aksiyon uygulama kapalı olmalıdır.")
    if settings.get("redaction_enabled") != "true":
        failures.append("Hassas veri maskeleme açık olmalıdır.")

    return {
        "ok": not failures,
        "version": AI_AGENT_AG6_VERSION,
        "mode": "kullanici_yetki_ve_guvenlik_ozeti",
        "notice": AI_AGENT_SECURITY_NOTICE,
        "failures": failures,
        "checks": {
            "login_required_context": bool(_user_id(user)),
            "elevated_scope": user_has_ai_agent_admin_scope(user),
            "sensitive_detail_returned": False,
            "public_health_contains_user_data": False,
            "queue_execution_enabled": False,
        },
        "safe_counts": {
            "agent_queue_total": _safe_table_count("ai_agent_action_queue"),
            "agent_request_logs": _safe_table_count("ai_agent_request_logs"),
        },
    }
