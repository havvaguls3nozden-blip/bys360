"""Ayarlar refactor sözleşmeleri.

Bu modül dataclass sözleşmeleri içerir; Flask uygulamasını veya veritabanını import etmez.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SettingDefinition:
    key: str
    label: str
    value_type: str = "string"
    default: Any = None
    group: str = "general"
    description: str = ""
    sensitive: bool = False
    editable: bool = True
    required: bool = False


@dataclass(frozen=True)
class SettingValue:
    key: str
    value: Any
    value_type: str = "string"
    source: str = "runtime"
    sensitive: bool = False


@dataclass(frozen=True)
class SettingChange:
    key: str
    old_value: Any
    new_value: Any
    actor_id: int | None = None
    operation: str = "update"
    reason: str = ""
    changed_at: datetime | None = None
    meta: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MenuPermissionRule:
    menu_key: str
    enabled: bool = True
    scope: str = "user"
    target_id: int | None = None
    reason: str = ""


@dataclass(frozen=True)
class SettingsAuditFinding:
    code: str
    status: str
    message: str
    path: str = ""
