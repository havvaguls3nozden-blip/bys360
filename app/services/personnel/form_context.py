
"""Personel form context yardımcıları.

Bu modül sadece template'e gönderilecek salt okunur bağlamları hazırlar.
Route davranışı, kayıt sırası, commit/rollback ve fotoğraf yükleme akışı Faz 1'de
aynı kalır.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .categories import PERSONNEL_CATEGORY_OPTIONS
from .form_payload import PersonnelFormPayload


def _as_list(value: Iterable[Any] | None) -> list[Any]:
    return list(value or [])


def _safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default) if obj is not None else default


def _resolve_manager_id(user_obj: Any, id_attr: str, sicil_attr: str, user_model: Any | None = None) -> int | None:
    direct_id = _safe_getattr(user_obj, id_attr)
    if direct_id:
        try:
            return int(direct_id)
        except (TypeError, ValueError):
            return None

    sicil_value = str(_safe_getattr(user_obj, sicil_attr, "") or "").strip()
    if not sicil_value or user_model is None or not hasattr(user_model, "sicil_no"):
        return None

    query = getattr(user_model, "query", None)
    if query is None or not hasattr(query, "filter_by"):
        return None
    manager = query.filter_by(sicil_no=sicil_value).first()
    manager_id = _safe_getattr(manager, "id")
    try:
        return int(manager_id) if manager_id else None
    except (TypeError, ValueError):
        return None


def build_personnel_create_form_context(
    *,
    role_values: Iterable[str] | None,
    managers: Iterable[Any] | None,
    payload: PersonnelFormPayload | None = None,
) -> dict[str, Any]:
    """Build context for personnel_add.html without querying or mutating DB."""
    context: dict[str, Any] = {
        "role_values": _as_list(role_values),
        "managers": _as_list(managers),
        "personnel_category_options": list(PERSONNEL_CATEGORY_OPTIONS),  # BYS360_PERSONNEL_CATEGORY_FORM_CONTEXT
    }
    if payload is not None:
        context["form_defaults"] = payload.to_template_defaults()
    return context


def build_personnel_edit_form_context(
    user: Any,
    *,
    role_values: Iterable[str] | None,
    managers: Iterable[Any] | None,
    avatar_url: str,
    current_role: str,
    user_model: Any | None = None,
) -> dict[str, Any]:
    """Build context for personnel_edit.html while preserving existing field names."""
    return {
        "user": user,
        "avatar_url": avatar_url,
        "role_values": _as_list(role_values),
        "managers": _as_list(managers),
        "current_role": current_role,
        "personnel_category_options": list(PERSONNEL_CATEGORY_OPTIONS),  # BYS360_PERSONNEL_CATEGORY_FORM_CONTEXT
        "current_personnel_category": _safe_getattr(user, "personnel_category", "Diğer") or "Diğer",
        "manager_1_id": _resolve_manager_id(user, "manager_1_id", "yonetici_sicil", user_model=user_model),
        "manager_2_id": _resolve_manager_id(user, "manager_2_id", "ikinci_yonetici_sicil", user_model=user_model),
        "manager_3_id": _resolve_manager_id(user, "manager_3_id", "ucuncu_yonetici_sicil", user_model=user_model),
    }


def build_personnel_form_phase1_summary() -> dict[str, Any]:
    return {
        "phase": "personnel_service_faz1",
        "purpose": "form_context_and_payload_read_bridge",
        "runtime_mutation": False,
        "db_commit": False,
        "db_rollback": False,
        "route_contract": "preserved",
        "template_contract": "preserved",
    }
