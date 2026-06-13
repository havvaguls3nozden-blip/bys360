"""Ayar tanımı yardımcıları.

Faz 1'de pasiftir; mevcut settings_service.py bu modülü çağırmaz.
"""
from __future__ import annotations


from collections.abc import Iterable, Mapping
from typing import Any

from .contracts import SettingDefinition
from .serialization import normalize_setting_key


def build_definition(raw: Mapping[str, Any] | SettingDefinition) -> SettingDefinition:
    if isinstance(raw, SettingDefinition):
        return raw
    return SettingDefinition(
        key=normalize_setting_key(raw.get("key")),
        label=str(raw.get("label") or raw.get("key") or "").strip(),
        value_type=str(raw.get("value_type") or raw.get("type") or "string").strip(),
        default=raw.get("default"),
        group=str(raw.get("group") or "general").strip(),
        description=str(raw.get("description") or "").strip(),
        sensitive=bool(raw.get("sensitive", False)),
        editable=bool(raw.get("editable", True)),
        required=bool(raw.get("required", False)),
    )


def index_definitions(definitions: Iterable[Mapping[str, Any] | SettingDefinition]) -> dict[str, SettingDefinition]:
    indexed: dict[str, SettingDefinition] = {}
    for item in definitions:
        definition = build_definition(item)
        if definition.key:
            indexed[definition.key] = definition
    return indexed


def group_definitions(definitions: Iterable[SettingDefinition]) -> dict[str, list[SettingDefinition]]:
    grouped: dict[str, list[SettingDefinition]] = {}
    for definition in definitions:
        grouped.setdefault(definition.group or "general", []).append(definition)
    for items in grouped.values():
        items.sort(key=lambda d: (d.label or d.key).casefold())
    return grouped
