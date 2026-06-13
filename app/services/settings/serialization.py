"""Yan etkisiz ayarlar serileştirme yardımcıları."""
from __future__ import annotations


import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from .constants import BOOLEAN_FALSE_VALUES, BOOLEAN_TRUE_VALUES, PROTECTED_SETTING_KEYS


def normalize_setting_key(key: object) -> str:
    """Ayar anahtarını güvenli ve tutarlı biçimde döndürür."""
    return str(key or "").strip()


def normalize_menu_key(key: object) -> str:
    """Menü anahtarlarını karşılaştırma için sadeleştirir."""
    return str(key or "").strip().replace(" ", "_").lower()


def to_bool(value: object, default: bool = False) -> bool:
    """Form/env/string değerlerini bool'a çevirir."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in BOOLEAN_TRUE_VALUES:
        return True
    if text in BOOLEAN_FALSE_VALUES:
        return False
    return default


def mask_sensitive_value(key: object, value: object, mask: str = "********") -> object:
    """Hassas anahtarların değerini log/rapor için maskeler."""
    normalized = normalize_setting_key(key)
    if normalized in PROTECTED_SETTING_KEYS:
        return mask if value not in (None, "") else value
    lowered = normalized.lower()
    if any(token in lowered for token in ("password", "secret", "token", "key")):
        return mask if value not in (None, "") else value
    return value


def json_safe(value: Any) -> Any:
    """JSON'a güvenli çevrilebilir değer üretir."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [json_safe(v) for v in value]
    return value


def dumps_json(value: Any) -> str:
    return json.dumps(json_safe(value), ensure_ascii=False, sort_keys=True)


def loads_json(value: object, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return default

def value_to_storage(value: Any, value_type: str) -> str:
    """Ayar değerini veritabanındaki metin temsiline çevirir.

    Eski settings_service.py davranışı korunur:
    - bool değerler true/false
    - int değerler güvenli sayı metni
    - diğerleri kırpılmış string
    """
    if value_type == "bool":
        return "true" if to_bool(value, default=False) else "false"
    if value_type == "int":
        try:
            return str(int(str(value or "0").strip() or 0))
        except (TypeError, ValueError):
            return "0"
    return str(value or "").strip()


def value_to_python(value_text: str | None, value_type: str) -> Any:
    """Veritabanındaki metin ayar değerini Python tipine çevirir."""
    raw = (value_text or "").strip()
    if value_type == "bool":
        return to_bool(raw, default=False)
    if value_type == "int":
        try:
            return int(raw or 0)
        except (TypeError, ValueError):
            return 0
    return raw

