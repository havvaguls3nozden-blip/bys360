"""Ayarlar okuma/snapshot yardımcıları.

Faz 3 kapsamı:
- Bu dosya veritabanı bağlantısı kurmaz.
- Commit/rollback/log oluşturmaz.
- settings_service.py içindeki okuma ve snapshot hesaplarını yan etkisiz yardımcılar haline getirir.
"""
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Iterable, Mapping
from typing import Any


def build_complete_visibility_map(all_menu_keys: Iterable[Any], visible_keys: Iterable[Any]) -> dict[str, bool]:
    """Tüm menü anahtarları için görünürlük haritası üretir."""
    visible = {str(key or "").strip() for key in (visible_keys or []) if str(key or "").strip()}
    return {str(menu_key or "").strip(): str(menu_key or "").strip() in visible for menu_key in (all_menu_keys or []) if str(menu_key or "").strip()}


def snapshot_system_rows(
    rows_by_key: Mapping[str, Any],
    definitions: Iterable[Mapping[str, Any]],
    *,
    value_to_storage: Callable[[Any, str], str],
) -> dict[str, Any]:
    """SystemSetting satırlarından log/snapshot için eski formatta sözlük üretir."""
    snapshot: dict[str, Any] = {}
    for definition in definitions or []:
        setting_key = str(definition.get("setting_key") or "").strip()
        if not setting_key:
            continue
        row = rows_by_key.get(setting_key)
        snapshot[setting_key] = value_to_storage(
            getattr(row, "value_text", None) if row is not None else definition.get("default"),
            str(definition.get("value_type") or "string"),
        )
    return snapshot


def snapshot_module_rows(
    rows_by_key: Mapping[tuple[str, str], Any],
    definitions: Iterable[Mapping[str, Any]],
    *,
    value_to_storage: Callable[[Any, str], str],
) -> dict[str, dict[str, Any]]:
    """ModuleSetting satırlarından modül/ayar kırılımında snapshot üretir."""
    snapshot: dict[str, dict[str, Any]] = {}
    for definition in definitions or []:
        module_key = str(definition.get("module_key") or "").strip()
        setting_key = str(definition.get("setting_key") or "").strip()
        if not module_key or not setting_key:
            continue
        row = rows_by_key.get((module_key, setting_key))
        snapshot.setdefault(module_key, {})[setting_key] = value_to_storage(
            getattr(row, "value_text", None) if row is not None else definition.get("default"),
            str(definition.get("value_type") or "string"),
        )
    return snapshot


def snapshot_user_override_rows(rows: Iterable[Any]) -> dict[str, bool]:
    """UserMenuPermission satırlarından kullanıcı override snapshot'ı üretir."""
    snapshot: dict[str, bool] = {}
    for row in rows or []:
        menu_key = str(getattr(row, "menu_key", "") or "").strip()
        if not menu_key:
            continue
        snapshot[menu_key] = bool(getattr(row, "is_visible", False))
    return snapshot


def build_role_default_snapshot_rows(
    role_names: Iterable[str],
    *,
    get_visible_keys: Callable[[str], Iterable[str]],
    all_menu_count: int,
) -> list[dict[str, Any]]:
    """Rol profili özet satırlarını üretir."""
    total = max(int(all_menu_count or 0), 1)
    rows: list[dict[str, Any]] = []
    for role_name in sorted({str(name or "").strip().lower() for name in role_names or [] if str(name or "").strip()}):
        visible_keys = set(get_visible_keys(role_name) or [])
        rows.append(
            {
                "role_name": role_name,
                "visible_count": len(visible_keys),
                "total_count": total,
                "coverage_ratio": round((len(visible_keys) / total) * 100, 1),
            }
        )
    return rows


def build_unit_profile_snapshot_rows(rows: Iterable[Any], *, all_menu_count: int) -> list[dict[str, Any]]:
    """Birim profil satırlarından özet tablo üretir."""
    total = max(int(all_menu_count or 0), 1)
    grouped: OrderedDict[str, list[Any]] = OrderedDict()
    for row in rows or []:
        unit_name = str(getattr(row, "unit_name", "") or "").strip()
        grouped.setdefault(unit_name, []).append(row)

    snapshot_rows: list[dict[str, Any]] = []
    for unit_name, items in grouped.items():
        visible_count = len([row for row in items if bool(getattr(row, "is_visible", False))])
        snapshot_rows.append(
            {
                "unit_name": unit_name,
                "configured_count": len(items),
                "visible_count": visible_count,
                "coverage_ratio": round((visible_count / total) * 100, 1),
            }
        )
    return snapshot_rows


def build_setting_groups(
    definitions: Iterable[Mapping[str, Any]],
    rows_by_key: Mapping[Any, Any],
    *,
    value_to_python: Callable[[Any, str], Any],
    group_key_field: str,
    group_label_field: str,
    group_description_field: str,
    row_key_builder: Callable[[Mapping[str, Any]], Any],
    output_group_key: str,
    output_group_label: str,
    output_group_description: str,
) -> list[dict[str, Any]]:
    """Ayar tanımlarını mevcut değerlerle gruplayarak ekran payload'u üretir.

    settings_service.py içindeki eski dict yapısını korur; sadece hesaplama yeri ayrılmıştır.
    """
    grouped: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for definition in definitions or []:
        group_key = str(definition.get(group_key_field) or "").strip()
        if not group_key:
            continue
        group = grouped.setdefault(
            group_key,
            {
                output_group_key: group_key,
                output_group_label: definition.get(group_label_field),
                output_group_description: definition.get(group_description_field, ""),
                "rows": [],
            },
        )
        row = rows_by_key.get(row_key_builder(definition))
        current_value = value_to_python(
            getattr(row, "value_text", None) if row else definition.get("default"),
            str(definition.get("value_type") or "string"),
        )
        group["rows"].append({**dict(definition), "current_value": current_value})
    return list(grouped.values())
