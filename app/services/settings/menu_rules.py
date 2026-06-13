"""Menü izin kuralları için yan etkisiz yardımcılar."""
from __future__ import annotations


from collections.abc import Iterable, Mapping
from typing import Any

from .contracts import MenuPermissionRule
from .serialization import normalize_menu_key, to_bool


def build_menu_rule(raw: Mapping[str, Any] | MenuPermissionRule) -> MenuPermissionRule:
    if isinstance(raw, MenuPermissionRule):
        return raw
    return MenuPermissionRule(
        menu_key=normalize_menu_key(raw.get("menu_key") or raw.get("key")),
        enabled=to_bool(raw.get("enabled", True), default=True),
        scope=str(raw.get("scope") or "user").strip() or "user",
        target_id=_safe_int(raw.get("target_id")),
        reason=str(raw.get("reason") or "").strip(),
    )


def normalize_menu_rules(items: Iterable[Mapping[str, Any] | MenuPermissionRule]) -> list[MenuPermissionRule]:
    rules: dict[tuple[str, str, int | None], MenuPermissionRule] = {}
    for item in items:
        rule = build_menu_rule(item)
        if not rule.menu_key:
            continue
        rules[(rule.scope, rule.menu_key, rule.target_id)] = rule
    return sorted(rules.values(), key=lambda r: (r.scope, r.menu_key, r.target_id or 0))


def enabled_menu_keys(items: Iterable[Mapping[str, Any] | MenuPermissionRule]) -> list[str]:
    return [rule.menu_key for rule in normalize_menu_rules(items) if rule.enabled]


def _safe_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return None

def filter_live_menu_keys(menu_keys: Iterable[Any], *, is_removed_checker: Any | None = None) -> list[str]:
    """Canlı kapsam dışı menü anahtarlarını temizler; mevcut anahtar biçimini korur."""
    cleaned: list[str] = []
    for raw_key in menu_keys or []:
        key = str(raw_key or "").strip()
        if not key:
            continue
        if is_removed_checker is not None and is_removed_checker(key):
            continue
        cleaned.append(key)
    return cleaned


def filter_live_menu_rows(rows: Iterable[Any], *, is_removed_checker: Any | None = None) -> list[Any]:
    """menu_key alanı canlı kapsam dışında kalan satırları eler."""
    if is_removed_checker is None:
        return list(rows or [])
    return [row for row in (rows or []) if not is_removed_checker(getattr(row, "menu_key", ""))]

