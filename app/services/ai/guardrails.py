from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import current_app
from flask_login import current_user

from app.route_support import user_has_any_role
from .client import get_provider_snapshot
from .module_scope import is_live_ai_module


DEFAULT_ALLOWED_MANAGER_ROLES = {
    "admin",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "birim_sorumlusu",
    "koordinator",
}

DEFAULT_ALLOWED_USER_ROLES = {
    "admin",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "birim_sorumlusu",
    "koordinator",
    "personel",
}


@dataclass(slots=True)
class AIFeaturePolicy:
    module_type: str
    feature_type: str
    allowed_roles: set[str]
    user_visible: bool = True


DEFAULT_POLICIES: dict[tuple[str, str], AIFeaturePolicy] = {
    ("performance", "summary"): AIFeaturePolicy("performance", "summary", set(DEFAULT_ALLOWED_MANAGER_ROLES)),
    ("performance", "consistency"): AIFeaturePolicy("performance", "consistency", set(DEFAULT_ALLOWED_MANAGER_ROLES)),
    ("dashboard", "brief"): AIFeaturePolicy("dashboard", "brief", set(DEFAULT_ALLOWED_USER_ROLES)),
    ("hr", "leave_brief"): AIFeaturePolicy("hr", "leave_brief", set(DEFAULT_ALLOWED_MANAGER_ROLES)),
    ("support", "triage"): AIFeaturePolicy("support", "triage", set(DEFAULT_ALLOWED_USER_ROLES)),
    ("communication", "priority"): AIFeaturePolicy("communication", "priority", set(DEFAULT_ALLOWED_MANAGER_ROLES)),
    ("survey", "summary"): AIFeaturePolicy("survey", "summary", set(DEFAULT_ALLOWED_MANAGER_ROLES)),
    ("feedback", "pulse_brief"): AIFeaturePolicy("feedback", "pulse_brief", set(DEFAULT_ALLOWED_MANAGER_ROLES)),
    ("analysis_center", "governance"): AIFeaturePolicy("analysis_center", "governance", set(DEFAULT_ALLOWED_MANAGER_ROLES)),
}


class AIAccessDenied(RuntimeError):
    pass


class AIServiceDisabled(RuntimeError):
    pass


class AIInputError(ValueError):
    pass


class AIResourceNotFound(LookupError):
    pass


def _configured_allowed_roles(default_roles: set[str]) -> set[str]:
    configured = current_app.config.get("AI_ALLOWED_ROLES") or ()
    normalized = {str(item).strip().lower() for item in configured if str(item).strip()}
    return normalized or set(default_roles)


def _configured_enabled_modules() -> set[str]:
    configured = current_app.config.get("AI_ENABLED_MODULES") or ()
    normalized = {str(item).strip().lower() for item in configured if str(item).strip()}
    return normalized or {policy.module_type for policy in DEFAULT_POLICIES.values()}


def _ensure_module_enabled(module_type: str) -> None:
    enabled_modules = _configured_enabled_modules()
    normalized_module = str(module_type or "").strip().lower()
    if normalized_module not in enabled_modules:
        raise AIServiceDisabled(f"{normalized_module or 'Bu modül'} için AI kullanımına pilot yapılandırmada izin verilmiyor.")


def _ensure_live_provider_if_required(policy: AIFeaturePolicy) -> None:
    if not policy.user_visible:
        return
    if not bool(current_app.config.get("AI_REQUIRE_REAL_PROVIDER_FOR_USER_VISIBLE", False)):
        return
    provider = get_provider_snapshot()
    if not provider.get("ready_for_live_provider"):
        raise AIServiceDisabled("Gerçek AI sağlayıcısı hazır olmadan kullanıcı görünür AI özeti açılamaz.")


def ensure_ai_access(module_type: str, feature_type: str, user: Any | None = None) -> AIFeaturePolicy:
    if not current_app.config.get("AI_ENABLED", True):
        raise AIServiceDisabled("AI destek katmanı şu anda kapalı.")

    normalized_module = str(module_type or "").strip().lower()
    normalized_feature = str(feature_type or "").strip().lower()
    policy = DEFAULT_POLICIES.get((normalized_module, normalized_feature))
    if policy is None:
        raise AIInputError("Tanımsız AI özelliği.")

    if not is_live_ai_module(normalized_module):
        raise AIServiceDisabled("Bu AI modülü güncel canlı omurga dışında bırakıldı.")
    _ensure_module_enabled(normalized_module)
    _ensure_live_provider_if_required(policy)

    actor = user or current_user
    allowed_roles = _configured_allowed_roles(policy.allowed_roles)
    if not user_has_any_role(actor, allowed_roles):
        raise AIAccessDenied("Bu AI özelliğini kullanma yetkiniz yok.")
    return AIFeaturePolicy(normalized_module, normalized_feature, allowed_roles, user_visible=policy.user_visible)


def sanitize_output_text(value: str, *, limit: int = 3000) -> str:
    cleaned = (value or "").strip()
    cleaned = cleaned.replace("<script", "&lt;script")
    cleaned = cleaned.replace("</script", "&lt;/script")
    return cleaned[:limit]
