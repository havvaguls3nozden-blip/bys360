
"""Ayarlar menü izinleri servis köprüsü.

Bu katman rol, birim ve kişi bazlı menü izin kayıtları için ortak filtreleme
ve snapshot yardımcılarını toplar. Route ve ana settings_service akışı DB commit
zincirini değiştirmeden bu yardımcıları kullanır.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.config import is_removed_menu_key
from app.models import ModuleSetting, RoleMenuDefault, SystemSetting, UnitMenuProfile, UserMenuPermission


def _clean_menu_key(value: Any) -> str:
    return str(value or "").strip()


def filter_live_menu_keys(menu_keys: Iterable[Any] | None) -> list[str]:
    """Kaldırılmış/kapsam dışı menü anahtarlarını ayıklar ve sıralamayı korur."""
    filtered: list[str] = []
    seen: set[str] = set()
    for raw_key in menu_keys or []:
        key = _clean_menu_key(raw_key)
        if not key or key in seen:
            continue
        if is_removed_menu_key(key):
            continue
        seen.add(key)
        filtered.append(key)
    return filtered


def filter_live_menu_rows(rows: Iterable[Any] | None) -> list[Any]:
    """DB satırlarını canlı menü kapsamına göre savunmacı biçimde süzer."""
    filtered: list[Any] = []
    for row in rows or []:
        key = _clean_menu_key(getattr(row, "menu_key", ""))
        if not key or is_removed_menu_key(key):
            continue
        filtered.append(row)
    return filtered


def build_complete_visibility_map(all_menu_keys: Iterable[Any] | None, visible_keys: Iterable[Any] | None) -> dict[str, bool]:
    """Tüm canlı menüler için eksiksiz görünür/gizli haritası üretir."""
    live_keys = filter_live_menu_keys(all_menu_keys)
    visible = set(filter_live_menu_keys(visible_keys))
    return {key: key in visible for key in live_keys}


def snapshot_role_menu_state(role_name: str, all_menu_keys: Iterable[Any] | None) -> dict[str, bool]:
    normalized_role = str(role_name or "").strip().lower()
    live_keys = filter_live_menu_keys(all_menu_keys)
    existing = {
        row.menu_key: bool(row.is_visible)
        for row in filter_live_menu_rows(RoleMenuDefault.query.filter_by(role_name=normalized_role).all())
    }
    return {key: bool(existing.get(key, False)) for key in live_keys}


def snapshot_unit_menu_state(unit_name: str, all_menu_keys: Iterable[Any] | None) -> dict[str, bool]:
    normalized_unit = str(unit_name or "").strip()
    live_keys = filter_live_menu_keys(all_menu_keys)
    existing = {
        row.menu_key: bool(row.is_visible)
        for row in filter_live_menu_rows(UnitMenuProfile.query.filter_by(unit_name=normalized_unit).all())
    }
    return {key: bool(existing.get(key, False)) for key in live_keys}


def snapshot_user_override_state(user_id: int | None) -> dict[str, bool]:
    if not user_id:
        return {}
    rows = filter_live_menu_rows(UserMenuPermission.query.filter_by(user_id=user_id).all())
    return {row.menu_key: bool(row.is_visible) for row in rows}


def snapshot_system_settings_state(definitions: Iterable[dict[str, Any]] | None) -> dict[str, str]:
    rows = {row.setting_key: row for row in SystemSetting.query.all()}
    snapshot: dict[str, str] = {}
    for definition in definitions or []:
        setting_key = str(definition.get("setting_key") or "").strip()
        if not setting_key:
            continue
        row = rows.get(setting_key)
        value = getattr(row, "value_text", None) if row is not None else definition.get("default", "")
        snapshot[setting_key] = "" if value is None else str(value)
    return snapshot


def snapshot_module_settings_state(definitions: Iterable[dict[str, Any]] | None) -> dict[str, dict[str, str]]:
    rows = {(row.module_key, row.setting_key): row for row in ModuleSetting.query.all()}
    snapshot: dict[str, dict[str, str]] = {}
    for definition in definitions or []:
        module_key = str(definition.get("module_key") or "").strip()
        setting_key = str(definition.get("setting_key") or "").strip()
        if not module_key or not setting_key:
            continue
        row = rows.get((module_key, setting_key))
        value = getattr(row, "value_text", None) if row is not None else definition.get("default", "")
        snapshot.setdefault(module_key, {})[setting_key] = "" if value is None else str(value)
    return snapshot
