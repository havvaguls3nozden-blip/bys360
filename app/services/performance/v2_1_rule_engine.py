from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

"""BYS360 Performans V2.1.1 merkezi kural motoru.

Bu servis, performans kurallarını kod içine dağınık sabitlemek yerine
``module_settings`` tablosundan okur. Tablo henüz yoksa veya veriye ulaşılamazsa
BYS360'ın güvenli kurumsal varsayılanlarına döner.
"""

logger = logging.getLogger(__name__)

RULE_VERSION = "performance_v2_1_1_rule_engine_settings"
MODULE_KEY = "performance"

LOW_SCORE_DEFAULT = 70.0
HIGH_SCORE_DEFAULT = 90.0

DEFAULT_SETTINGS: dict[str, dict[str, Any]] = {
    "require_criterion_comment_for_score_1_5": {
        "label": "1 ve 5 puanlarda açıklama zorunluluğu",
        "value_text": "true",
        "value_type": "bool",
        "description": "Açık ise kriter bazında 1 veya 5 puan verildiğinde açıklama zorunlu olur.",
    },
    "require_general_comment_below_70": {
        "label": "70 altı genel görüş zorunluluğu",
        "value_text": "true",
        "value_type": "bool",
        "description": "Açık ise nihai puan düşük performans eşiğinin altındaysa genel görüş zorunlu olur.",
    },
    "require_general_comment_above_90": {
        "label": "90 üstü genel görüş zorunluluğu",
        "value_text": "true",
        "value_type": "bool",
        "description": "Açık ise nihai puan yüksek başarı eşiğinin üstündeyse genel görüş zorunlu olur.",
    },
    "low_score_threshold": {
        "label": "Düşük performans eşiği",
        "value_text": "70",
        "value_type": "float",
        "description": "Bu puanın altındaki sonuçlar düşük performans sürecine girer.",
    },
    "high_score_threshold": {
        "label": "Çok başarılı performans eşiği",
        "value_text": "90",
        "value_type": "float",
        "description": "Bu puanın üstündeki sonuçlarda ayrıntılı genel görüş beklenir.",
    },
    "require_president_approval_below_70": {
        "label": "70 altı Başkan/Üst Onay zorunluluğu",
        "value_text": "true",
        "value_type": "bool",
        "description": "Açık ise 70 altı sonuçlar doğrudan kesinleşmez, Başkan/Üst Onay sürecine alınır.",
    },
    "block_publish_until_president_approval": {
        "label": "Başkan/Üst Onay tamamlanmadan yayın kilidi",
        "value_text": "true",
        "value_type": "bool",
        "description": "Açık ise 70 altı sonuç Başkan/Üst Onay tamamlanmadan personele yayınlanamaz.",
    },
    "require_personnel_support_publish_preapproval": {
        "label": "Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayı",
        "value_text": "true",
        "value_type": "bool",
        "description": "Açık ise nihai yayından önce kurumsal yayın ön onayı beklenir.",
    },
    "third_supervisor_default_mode": {
        "label": "3. amir varsayılan modu",
        "value_text": "comment_only",
        "value_type": "string",
        "description": "Değerler: disabled, comment_only, scoring. Dönem özel ayarı yoksa kullanılır.",
    },
    "technical_status_localization_enabled": {
        "label": "Teknik statüleri Türkçeleştir",
        "value_text": "true",
        "value_type": "bool",
        "description": "Açık ise teknik süreç kodları kullanıcı ekranına Türkçe kurumsal ifadeyle yansıtılır.",
    },
}

STATUS_LABELS = {
    "president_pending": "Başkan Onayı Bekliyor",
    "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
    "hr_precheck": "İK/Admin Ön Kontrolünde",
    "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
    "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
    "approved_by_president": "Başkan Tarafından Onaylandı",
    "rejected_by_president": "Başkan Tarafından İade Edildi",
    "scorecard_pending": "Karne Yayın Hazırlığında",
    "workflow_state": "Süreç Durumu",
    "draft": "Taslak",
    "pending": "Bekliyor",
    "completed": "Tamamlandı",
    "published": "Yayınlandı",
    "not_required": "Gerekli Değil",
}

_TRUE_VALUES = {"1", "true", "on", "yes", "evet", "aktif", "active", "açık", "acik"}
_FALSE_VALUES = {"0", "false", "off", "no", "hayir", "hayır", "pasif", "inactive", "kapalı", "kapali"}


def _default_text(setting_key: str) -> str | None:
    data = DEFAULT_SETTINGS.get(setting_key) or {}
    value = data.get("value_text")
    return None if value is None else str(value)


def _has_module_settings_table() -> bool:
    try:
        from sqlalchemy import inspect

        from app.extensions import db
        return bool(inspect(db.engine).has_table("module_settings"))
    except (SQLAlchemyError, ImportError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def get_setting_text(setting_key: str, default: Any | None = None) -> str | None:
    """Performans modül ayarını metin olarak döndürür."""
    fallback = _default_text(setting_key)
    if default is not None:
        fallback = str(default)
    if not _has_module_settings_table():
        return fallback
    try:
        from sqlalchemy import text

        from app.extensions import db
        row = db.session.execute(
            text(
                """
                SELECT value_text
                FROM module_settings
                WHERE module_key = :module_key
                  AND setting_key = :setting_key
                  AND is_active = true
                ORDER BY id DESC
                LIMIT 1
                """
            ),
            {"module_key": MODULE_KEY, "setting_key": setting_key},
        ).first()
        if not row:
            return fallback
        raw = row[0]
        return fallback if raw is None else str(raw)
    except (SQLAlchemyError, ImportError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return fallback


def get_setting_bool(setting_key: str, default: bool | None = None) -> bool:
    fallback_raw = _default_text(setting_key)
    fallback = bool(default) if default is not None else str(fallback_raw).strip().lower() in _TRUE_VALUES
    raw = get_setting_text(setting_key, "true" if fallback else "false")
    normalized = str(raw or "").strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    return bool(fallback)


def get_setting_float(setting_key: str, default: float | None = None) -> float:
    fallback_raw = _default_text(setting_key)
    try:
        if default is not None:
            fallback = float(default)
        elif fallback_raw is not None:
            fallback = float(fallback_raw)
        else:
            fallback = 0.0
    except (TypeError, ValueError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        fallback = 0.0
    raw = get_setting_text(setting_key, str(fallback))
    try:
        return float(str(raw).replace(",", "."))
    except (TypeError, ValueError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return fallback


def get_setting_str(setting_key: str, default: str | None = None) -> str:
    raw = get_setting_text(setting_key, default if default is not None else _default_text(setting_key))
    return str(raw or "").strip()


def normalize_raw_score(raw_score: Any) -> int | None:
    try:
        if raw_score in (None, ""):
            return None
        return int(float(raw_score))
    except (TypeError, ValueError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def score_requires_criterion_comment(raw_score: Any) -> bool:
    normalized = normalize_raw_score(raw_score)
    if normalized in {1, 5}:
        return get_setting_bool("require_criterion_comment_for_score_1_5", True)
    return False


def is_low_score(score_100: Any) -> bool:
    try:
        return float(score_100 or 0) < get_setting_float("low_score_threshold", LOW_SCORE_DEFAULT)
    except (TypeError, ValueError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def is_high_score(score_100: Any) -> bool:
    try:
        return float(score_100 or 0) > get_setting_float("high_score_threshold", HIGH_SCORE_DEFAULT)
    except (TypeError, ValueError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def general_comment_required(score_100: Any) -> bool:
    if is_low_score(score_100):
        return get_setting_bool("require_general_comment_below_70", True)
    if is_high_score(score_100):
        return get_setting_bool("require_general_comment_above_90", True)
    return False


def president_approval_required(score_100: Any) -> bool:
    return bool(is_low_score(score_100) and get_setting_bool("require_president_approval_below_70", True))


def publish_blocked_until_president_approval(score_100: Any) -> bool:
    return bool(president_approval_required(score_100) and get_setting_bool("block_publish_until_president_approval", True))


def personnel_support_preapproval_required() -> bool:
    return get_setting_bool("require_personnel_support_publish_preapproval", True)


def status_label(status_key: Any) -> str:
    raw = str(status_key or "").strip()
    if not raw:
        return "Durum Bilgisi Yok"
    if not get_setting_bool("technical_status_localization_enabled", True):
        return raw
    return STATUS_LABELS.get(raw, raw.replace("_", " ").strip().title())


def validate_score_comment_rules(raw_score: Any = None, score_100: Any = None, criterion_comment: str | None = None, general_comment: str | None = None) -> list[str]:
    issues: list[str] = []
    if score_requires_criterion_comment(raw_score) and not str(criterion_comment or "").strip():
        issues.append("1 ve 5 puanlarda açıklama zorunluluğu aktiftir; kriter açıklaması girilmelidir.")
    if score_100 is not None and general_comment_required(score_100) and not str(general_comment or "").strip():
        issues.append("70 altı veya 90 üstü sonuçlarda ayrıntılı genel görüş girilmelidir.")
    return issues


def evaluation_final_score(evaluation: Any) -> float:
    for attr in ("final_total_100", "final_score", "score_100", "total_score"):
        value = getattr(evaluation, attr, None)
        if value not in (None, ""):
            try:
                return float(value)
            except (TypeError, ValueError):
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                continue
    return 0.0


def evaluate_publish_guard(evaluation: Any, *, president_approved: bool | None = None, personnel_support_preapproved: bool | None = None) -> dict[str, Any]:
    """Yayın öncesi merkezi kural özetini döndürür.

    Bu fonksiyon tek başına veri yazmaz. Var olan yayın servisleri bu sonucu
    kullanarak güvenli karar verebilir.
    """
    score = evaluation_final_score(evaluation)
    blocks: list[str] = []

    if publish_blocked_until_president_approval(score) and not bool(president_approved):
        blocks.append("70 altı sonuç Başkan/Üst Onay tamamlanmadan personele yayınlanamaz.")

    if personnel_support_preapproval_required() and personnel_support_preapproved is False:
        blocks.append("Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayı tamamlanmadan final yayın yapılmamalıdır.")

    return {
        "ok": not blocks,
        "rule_version": RULE_VERSION,
        "score_100": score,
        "is_low_score": is_low_score(score),
        "is_high_score": is_high_score(score),
        "president_approval_required": president_approval_required(score),
        "personnel_support_preapproval_required": personnel_support_preapproval_required(),
        "blocks": blocks,
    }


@dataclass(frozen=True)
class RuleSnapshot:
    rule_version: str
    settings: dict[str, Any]
    labels: dict[str, str]


def build_rule_snapshot() -> RuleSnapshot:
    values: dict[str, Any] = {}
    for key, meta in DEFAULT_SETTINGS.items():
        value_type = str(meta.get("value_type") or "string")
        if value_type == "bool":
            values[key] = get_setting_bool(key)
        elif value_type == "float":
            values[key] = get_setting_float(key)
        else:
            values[key] = get_setting_str(key)
    return RuleSnapshot(rule_version=RULE_VERSION, settings=values, labels=dict(STATUS_LABELS))


def build_rule_snapshot_dict() -> dict[str, Any]:
    snapshot = build_rule_snapshot()
    return {"rule_version": snapshot.rule_version, "settings": snapshot.settings, "labels": snapshot.labels}
