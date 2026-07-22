"""Ayar servisinin gelecek fazlarda kullanacağı bootstrap yardımcıları."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .definitions import index_definitions
from .serialization import mask_sensitive_value, normalize_setting_key


def build_runtime_settings_snapshot(
    values: Mapping[str, Any],
    definitions: Iterable[Mapping[str, Any]] = (),
    *,
    mask_sensitive: bool = True,
) -> dict[str, Any]:
    indexed_definitions = index_definitions(definitions)
    snapshot: dict[str, Any] = {}
    for raw_key, raw_value in values.items():
        key = normalize_setting_key(raw_key)
        if not key:
            continue
        definition = indexed_definitions.get(key)
        value = raw_value
        if mask_sensitive and (definition.sensitive if definition else False) or mask_sensitive:
            value = mask_sensitive_value(key, raw_value)
        snapshot[key] = value
    return snapshot


def merge_defaults(defaults: Mapping[str, Any], overrides: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(defaults or {})
    for key, value in (overrides or {}).items():
        normalized = normalize_setting_key(key)
        if normalized:
            merged[normalized] = value
    return merged
