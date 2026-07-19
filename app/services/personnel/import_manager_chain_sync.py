
"""Excel/personel import sonrası amir seçili görünüm senkronu.

Bu servis Excel'de gelen yönetici sicillerini kaynak kabul eder;
sicil alanlarını ezmez. Modelde varsa manager_1_id / manager_2_id /
manager_3_id alanlarını aynı sicillere karşılık gelen kullanıcı id'leriyle
eşler. Böylece personel düzenleme ekranındaki amir dropdownları seçili gelir.
"""
from __future__ import annotations

from typing import Any
from collections.abc import Iterable


def _safe_sicil(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value)).strip()
    if isinstance(value, int):
        return str(value).strip()
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def build_sicil_user_lookup(*, user_model: Any) -> dict[str, Any]:
    query = getattr(user_model, "query", None)
    if query is None or not hasattr(query, "all"):
        return {}
    users = query.all()
    lookup: dict[str, Any] = {}
    for user in users:
        sicil = _safe_sicil(getattr(user, "sicil_no", None))
        if sicil:
            lookup.setdefault(sicil, user)
    return lookup


def _set_id_if_model_supports(user: Any, field_name: str, manager: Any | None) -> bool:
    if not hasattr(user, field_name):
        return False
    setattr(user, field_name, getattr(manager, "id", None) if manager else None)
    return True


def sync_user_manager_ids_from_sicils(
    user: Any,
    *,
    users_by_sicil: dict[str, Any],
) -> dict[str, Any]:
    """Mirror 1/2/3. amir sicil alanlarını id alanlarına güvenli şekilde yansıt."""

    pairs = (
        ("yonetici_sicil", "manager_1_id", 1),
        ("ikinci_yonetici_sicil", "manager_2_id", 2),
        ("ucuncu_yonetici_sicil", "manager_3_id", 3),
    )
    synced = 0
    missing: list[str] = []
    self_refs: list[str] = []
    supported_id_fields = 0

    user_sicil = _safe_sicil(getattr(user, "sicil_no", None))
    for sicil_field, id_field, level in pairs:
        manager_sicil = _safe_sicil(getattr(user, sicil_field, None))
        if not manager_sicil:
            if _set_id_if_model_supports(user, id_field, None):
                supported_id_fields += 1
            continue
        manager = users_by_sicil.get(manager_sicil)
        if manager_sicil == user_sicil:
            self_refs.append(f"{user_sicil}: {level}. amir kendisi olamaz")
            manager = None
        elif manager is None:
            missing.append(f"{user_sicil or '-'}: {level}. amir sicili bulunamadı -> {manager_sicil}")

        if _set_id_if_model_supports(user, id_field, manager):
            supported_id_fields += 1
            if manager is not None:
                synced += 1

    return {
        "synced": synced,
        "supported_id_fields": supported_id_fields,
        "missing": missing,
        "self_refs": self_refs,
    }


def sync_touched_users_manager_ids_from_sicils(
    touched_users: Iterable[Any],
    *,
    user_model: Any,
) -> dict[str, Any]:
    users = list(touched_users or [])
    users_by_sicil = build_sicil_user_lookup(user_model=user_model)
    synced_count = 0
    supported_id_field_count = 0
    warnings: list[str] = []

    for user in users:
        result = sync_user_manager_ids_from_sicils(user, users_by_sicil=users_by_sicil)
        synced_count += int(result.get("synced") or 0)
        supported_id_field_count += int(result.get("supported_id_fields") or 0)
        warnings.extend(result.get("missing") or [])
        warnings.extend(result.get("self_refs") or [])

    return {
        "touched_count": len(users),
        "synced_count": synced_count,
        "supported_id_field_count": supported_id_field_count,
        "warnings": warnings,
    }
