# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
"""BYS360 Performans Faz 1.2 - ayar anahtarları ve okuma katmanı.

Bu dosya Faz 1.3 kural motorunun kullanacağı ayar sözleşmesini tek yerde
tutar. Veritabanı şemasını değiştirmez; mevcut ``module_settings`` tablosunu
okur. DB erişimi yoksa güvenli varsayılanlara döner.
"""

from dataclasses import dataclass
from typing import Any
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PerformanceRuleSetting:
    full_key: str
    module_key: str
    setting_key: str
    label: str
    value_type: str
    default: Any
    description: str


PERFORMANCE_RULE_SETTINGS: tuple[PerformanceRuleSetting, ...] = (
    PerformanceRuleSetting(
        full_key="performance.require_comment_for_score_1",
        module_key="performance_scoring",
        setting_key="require_comment_for_score_1",
        label="1 puanda açıklama zorunlu",
        value_type="bool",
        default=True,
        description="1 verilen kriterlerde açıklama alanını zorunlu tutar.",
    ),
    PerformanceRuleSetting(
        full_key="performance.require_comment_for_score_5",
        module_key="performance_scoring",
        setting_key="require_comment_for_score_5",
        label="5 puanda açıklama zorunlu",
        value_type="bool",
        default=True,
        description="5 verilen kriterlerde açıklama alanını zorunlu tutar.",
    ),
    PerformanceRuleSetting(
        full_key="performance.require_general_comment_below_70",
        module_key="performance_scoring",
        setting_key="require_general_comment_below_70",
        label="70 altı genel görüş zorunlu",
        value_type="bool",
        default=True,
        description="Nihai puan 70’in altında kaldığında ayrıntılı genel görüş ister.",
    ),
    PerformanceRuleSetting(
        full_key="performance.require_general_comment_above_90",
        module_key="performance_scoring",
        setting_key="require_general_comment_above_90",
        label="90 üstü genel görüş zorunlu",
        value_type="bool",
        default=True,
        description="Nihai puan 90’ın üstüne çıktığında ayrıntılı genel görüş ister.",
    ),
    PerformanceRuleSetting(
        full_key="performance.low_score_requires_president_approval",
        module_key="performance_flow",
        setting_key="low_score_requires_president_approval",
        label="70 altı Başkan onayı zorunlu",
        value_type="bool",
        default=True,
        description="70 altı sonucun kesinleşmeden önce Başkan onayına düşmesini sağlar.",
    ),
    PerformanceRuleSetting(
        full_key="performance.low_score_publish_lock",
        module_key="performance_flow",
        setting_key="low_score_publish_lock",
        label="70 altı yayın kilidi aktif",
        value_type="bool",
        default=True,
        description="70 altı karne Başkan onayı tamamlanmadan personele yayınlanmaz.",
    ),
    PerformanceRuleSetting(
        full_key="performance.status_language_mode",
        module_key="performance_flow",
        setting_key="status_language_mode",
        label="Statü dili",
        value_type="string",
        default="institutional_tr",
        description="Teknik statü kodlarının kullanıcıya kurumsal Türkçe gösterilmesini sağlar.",
    ),
)


PERFORMANCE_RULE_SETTING_BY_FULL_KEY: dict[str, PerformanceRuleSetting] = {
    item.full_key: item for item in PERFORMANCE_RULE_SETTINGS
}

PERFORMANCE_RULE_SETTING_BY_MODULE_KEY: dict[tuple[str, str], PerformanceRuleSetting] = {
    (item.module_key, item.setting_key): item for item in PERFORMANCE_RULE_SETTINGS
}


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "on", "yes", "evet", "aktif"}


def _coerce_setting_value(value: Any, value_type: str, default: Any) -> Any:
    if value_type == "bool":
        return _coerce_bool(value, bool(default))
    if value_type == "int":
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default
    text = "" if value is None else str(value).strip()
    return text if text != "" else default


def default_performance_rule_settings() -> dict[str, Any]:
    """Faz 1.3 kural motoru için güvenli varsayılanları döndürür."""
    return {item.full_key: item.default for item in PERFORMANCE_RULE_SETTINGS}


def catalog_rows_for_gate() -> list[dict[str, Any]]:
    """Gate ve seed scriptleri için düz sözlük listesi üretir."""
    return [
        {
            "full_key": item.full_key,
            "module_key": item.module_key,
            "setting_key": item.setting_key,
            "label": item.label,
            "value_type": item.value_type,
            "default": item.default,
            "description": item.description,
        }
        for item in PERFORMANCE_RULE_SETTINGS
    ]


def get_performance_rule_setting(full_key: str, default: Any | None = None) -> Any:
    """Tek bir performans ayarını güvenli şekilde okur.

    DB veya Flask uygulama bağlamı yoksa sözleşmedeki varsayılan değere döner.
    Bu fonksiyon Faz 1.3 kural motorunda doğrudan kullanılabilir.
    """
    definition = PERFORMANCE_RULE_SETTING_BY_FULL_KEY.get(full_key)
    if not definition:
        return default
    fallback = definition.default if default is None else default

    try:
        from app.models import ModuleSetting
        row = ModuleSetting.query.filter_by(
            module_key=definition.module_key,
            setting_key=definition.setting_key,
        ).first()
        if row is None:
            return fallback
        return _coerce_setting_value(row.value_text, definition.value_type, fallback)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return fallback


def get_performance_rule_settings() -> dict[str, Any]:
    """Tüm Faz 1.2 performans ayarlarını full_key sözlüğü olarak döndürür."""
    values = default_performance_rule_settings()
    for item in PERFORMANCE_RULE_SETTINGS:
        values[item.full_key] = get_performance_rule_setting(item.full_key, item.default)
    return values


__all__ = [
    "PERFORMANCE_RULE_SETTINGS",
    "PERFORMANCE_RULE_SETTING_BY_FULL_KEY",
    "PERFORMANCE_RULE_SETTING_BY_MODULE_KEY",
    "PerformanceRuleSetting",
    "catalog_rows_for_gate",
    "default_performance_rule_settings",
    "get_performance_rule_setting",
    "get_performance_rule_settings",
]

# BYS360_PHASE4_THIRD_SUPERVISOR_SETTINGS_EXT
try:
    _PHASE4_THIRD_SUPERVISOR_SETTINGS = (
        PerformanceRuleSetting(
            full_key="performance.third_supervisor_enabled",
            module_key="performance",
            setting_key="third_supervisor_enabled",
            label="3. amir kullanımı aktif",
            value_type="bool",
            default=True,
            description="3. amir alanının sistem genelinde kullanılabilmesini sağlar; gerçek amir yoksa görev üretilmez.",
        ),
        PerformanceRuleSetting(
            full_key="performance.third_supervisor_mode",
            module_key="performance",
            setting_key="third_supervisor_mode",
            label="3. amir modu",
            value_type="string",
            default="comment_only",
            description="3. amir için comment_only/yorumcu veya scoring/puan modu değerini belirler.",
        ),
        PerformanceRuleSetting(
            full_key="performance.third_supervisor_show_column",
            module_key="performance",
            setting_key="third_supervisor_show_column",
            label="3. amir sütunu gösterilsin",
            value_type="bool",
            default=False,
            description="3. amir olmayan ekranlarda boş sütun oluşmaması için varsayılan olarak kapalıdır.",
        ),
        PerformanceRuleSetting(
            full_key="performance.third_supervisor_weight_enabled",
            module_key="performance",
            setting_key="third_supervisor_weight_enabled",
            label="3. amir puan ağırlığı aktif",
            value_type="bool",
            default=False,
            description="3. amir puan modundaysa ağırlık hesabına dahil edilmesini sağlar; kapalıysa puan etkisi %0 kabul edilir.",
        ),
    )
    _phase4_existing_keys = {item.full_key for item in PERFORMANCE_RULE_SETTINGS}
    PERFORMANCE_RULE_SETTINGS = PERFORMANCE_RULE_SETTINGS + tuple(
        item for item in _PHASE4_THIRD_SUPERVISOR_SETTINGS if item.full_key not in _phase4_existing_keys
    )
    PERFORMANCE_RULE_SETTING_BY_FULL_KEY = {item.full_key: item for item in PERFORMANCE_RULE_SETTINGS}
    PERFORMANCE_RULE_SETTING_BY_MODULE_KEY = {(item.module_key, item.setting_key): item for item in PERFORMANCE_RULE_SETTINGS}
except Exception:
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    import logging
    logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/performance_rule_settings.py")
try:
    _PHASE4_1_THIRD_SUPERVISOR_SETTINGS = (
        PerformanceRuleSetting(
            full_key="performance.third_supervisor_enabled",
            module_key="performance",
            setting_key="third_supervisor_enabled",
            label="3. amir kullanımı aktif",
            value_type="bool",
            default=True,
            description="3. amir alanının sistem genelinde kullanılabilmesini sağlar; gerçek amir yoksa görev üretilmez.",
        ),
        PerformanceRuleSetting(
            full_key="performance.third_supervisor_mode",
            module_key="performance",
            setting_key="third_supervisor_mode",
            label="3. amir modu",
            value_type="string",
            default="comment_only",
            description="3. amir için comment_only/yorumcu veya scoring/puan modu değerini belirler.",
        ),
        PerformanceRuleSetting(
            full_key="performance.third_supervisor_show_column",
            module_key="performance",
            setting_key="third_supervisor_show_column",
            label="3. amir sütunu gösterilsin",
            value_type="bool",
            default=False,
            description="3. amir sütununun ekranlarda gösterilip gösterilmeyeceğini belirler.",
        ),
        PerformanceRuleSetting(
            full_key="performance.third_supervisor_weight_enabled",
            module_key="performance",
            setting_key="third_supervisor_weight_enabled",
            label="3. amir puan ağırlığı aktif",
            value_type="bool",
            default=False,
            description="3. amir puan modundaysa ağırlık hesabına dahil edilmesini sağlar; yorum modunda puan etkisi %0 kabul edilir.",
        ),
    )
    _phase4_1_existing_keys = {item.full_key for item in PERFORMANCE_RULE_SETTINGS}
    PERFORMANCE_RULE_SETTINGS = PERFORMANCE_RULE_SETTINGS + tuple(
        item for item in _PHASE4_1_THIRD_SUPERVISOR_SETTINGS if item.full_key not in _phase4_1_existing_keys
    )
    PERFORMANCE_RULE_SETTING_BY_FULL_KEY = {item.full_key: item for item in PERFORMANCE_RULE_SETTINGS}
    PERFORMANCE_RULE_SETTING_BY_MODULE_KEY = {(item.module_key, item.setting_key): item for item in PERFORMANCE_RULE_SETTINGS}
except Exception:
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    import logging
    logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/performance_rule_settings.py")