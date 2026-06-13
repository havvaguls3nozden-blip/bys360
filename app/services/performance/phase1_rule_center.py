# -*- coding: utf-8 -*-
from __future__ import annotations


import logging

"""BYS360 Performans Tamamlama Faz 1 - Kural Motoru ve Ayar Merkezi.

Bu servis Faz 1 icin tek kaynak sozlesmesidir:
- 1/5 puan aciklama zorunlulugu ayardan okunur.
- 70 alti genel gorus ve Baskan/Ust Onay zorunlulugu ayardan okunur.
- 70 alti karne yayin kilidi merkezi karar olarak doner.
- Teknik durum kodlari kullaniciya kurumsal Turkce etiketle gosterilir.
- DB/Flask baglami yoksa guvenli varsayilanlarla calisir.

Not: Bu dosya idari karar vermez; yalnizca mevcut performans is kurallarini
route, servis, template ve gate katmanlarinin ayni sozlesmeden okuyabilmesi
icin merkezi hale getirir.
"""

from dataclasses import dataclass, field
from typing import Any, Mapping
logger = logging.getLogger(__name__)

LOW_SCORE_THRESHOLD = 70.0
HIGH_SCORE_THRESHOLD = 90.0
MIN_CRITERIA_SCORE = 1
MAX_CRITERIA_SCORE = 5

SETTING_REQUIRE_COMMENT_FOR_SCORE_1 = "performance.require_comment_for_score_1"
SETTING_REQUIRE_COMMENT_FOR_SCORE_5 = "performance.require_comment_for_score_5"
SETTING_REQUIRE_GENERAL_COMMENT_BELOW_70 = "performance.require_general_comment_below_70"
SETTING_REQUIRE_GENERAL_COMMENT_ABOVE_90 = "performance.require_general_comment_above_90"
SETTING_LOW_SCORE_REQUIRES_PRESIDENT_APPROVAL = "performance.low_score_requires_president_approval"
SETTING_LOW_SCORE_PUBLISH_LOCK = "performance.low_score_publish_lock"
SETTING_STATUS_LANGUAGE_MODE = "performance.status_language_mode"
SETTING_PUBLISH_PREFLIGHT_USES_RULE_CENTER = "performance.publish_preflight_uses_rule_center"
SETTING_PERSONNEL_SUPPORT_PREAPPROVAL_REQUIRED = "performance.personnel_support_publish_preapproval_required"

PHASE1_RULE_CENTER_VERSION = "performance-completion-phase1-rule-center-v1"

TECHNICAL_STATUS_FALLBACK_LABEL = "Süreç Durumu Belirleniyor"

INSTITUTIONAL_TR_STATUS_LABELS: dict[str, str] = {
    "draft": "Taslak",
    "authorized_scope": "Yetkili Kapsam",
    "employee_visible": "Personel Karnesinde Görünür",
    "private": "Yetkili Kullanıcılarla Sınırlı",
    "published": "Yayımlandı",
    "closed": "Kapalı",
    "pending": "Bekliyor",
    "in_progress": "İşlemde",
    "completed": "Tamamlandı",
    "scorecard_pending": "Karne Yayın Süreci Bekliyor",
    "workflow_state": "Süreç Durumu",
    "phase_sync": "Süreç Eşleştirme Kaydı",
    "president_pending": "Başkan Onayı Bekliyor",
    "direct_president_pending": "Başkan Onayı Bekliyor",
    "president_approval_pending": "Başkan Onayı Bekliyor",
    "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
    "hr_precheck": "İK/Admin Ön Kontrolünde",
    "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
    "warning_recorded": "Düşük Performans Uyarısı Oluşturuldu",
    "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
    "second_low_score_process_started": "Tekrarlayan Düşük Performans Süreci",
    "repeated_low_score_process_started": "Tekrarlayan Düşük Performans Süreci",
    "approved_by_president": "Başkan Tarafından Onaylandı",
    "president_approved": "Başkan/Üst Onay Tamamlandı",
    "rejected_by_president": "Başkan Tarafından İade Edildi",
    "president_rejected": "Başkan/Üst Onay Tarafından İade Edildi",
    "president_returned": "Başkan/Üst Onay Tarafından İade Edildi",
    "publish_locked": "Yayın Kilidi Aktif",
    "publish_ready": "Yayına Hazır",
    "published_to_employee": "Personele Yayımlandı",
    "comment_pending": "Yorum/Görüş Bekliyor",
    "score_pending": "Puanlama Bekliyor",
    "personnel_support_preapproval_pending": "Personel ve Destek Hizmetleri Grup Başkanı Ön Onayı Bekliyor",
    "personnel_support_preapproved": "Personel ve Destek Hizmetleri Grup Başkanı Ön Onayı Tamamlandı",
}

TECHNICAL_STATUS_CODES_BLOCKED_FROM_UI: tuple[str, ...] = (
    "draft",
    "authorized_scope",
    "phase_sync",
    "workflow_state",
    "scorecard_pending",
    "president_pending",
    "blocked_president_pending",
)


@dataclass(frozen=True)
class Phase1RuleSetting:
    full_key: str
    module_key: str
    setting_key: str
    label: str
    value_type: str
    default: Any
    description: str


PHASE1_RULE_SETTINGS: tuple[Phase1RuleSetting, ...] = (
    Phase1RuleSetting(
        full_key=SETTING_REQUIRE_COMMENT_FOR_SCORE_1,
        module_key="performance_scoring",
        setting_key="require_comment_for_score_1",
        label="1 puanda açıklama zorunlu",
        value_type="bool",
        default=True,
        description="1 verilen değerlendirme kriterlerinde açıklama alanını zorunlu tutar.",
    ),
    Phase1RuleSetting(
        full_key=SETTING_REQUIRE_COMMENT_FOR_SCORE_5,
        module_key="performance_scoring",
        setting_key="require_comment_for_score_5",
        label="5 puanda açıklama zorunlu",
        value_type="bool",
        default=True,
        description="5 verilen değerlendirme kriterlerinde açıklama alanını zorunlu tutar.",
    ),
    Phase1RuleSetting(
        full_key=SETTING_REQUIRE_GENERAL_COMMENT_BELOW_70,
        module_key="performance_scoring",
        setting_key="require_general_comment_below_70",
        label="70 altı genel görüş zorunlu",
        value_type="bool",
        default=True,
        description="Nihai puan 70 altında kaldığında ayrıntılı genel görüş ister.",
    ),
    Phase1RuleSetting(
        full_key=SETTING_REQUIRE_GENERAL_COMMENT_ABOVE_90,
        module_key="performance_scoring",
        setting_key="require_general_comment_above_90",
        label="90 üstü genel görüş zorunlu",
        value_type="bool",
        default=True,
        description="Nihai puan 90 üstüne çıktığında ayrıntılı genel görüş ister.",
    ),
    Phase1RuleSetting(
        full_key=SETTING_LOW_SCORE_REQUIRES_PRESIDENT_APPROVAL,
        module_key="performance_flow",
        setting_key="low_score_requires_president_approval",
        label="70 altı Başkan/Üst Onay zorunlu",
        value_type="bool",
        default=True,
        description="70 altı sonuçların kesinleşmeden önce Başkan/Üst Onay sürecine düşmesini sağlar.",
    ),
    Phase1RuleSetting(
        full_key=SETTING_LOW_SCORE_PUBLISH_LOCK,
        module_key="performance_flow",
        setting_key="low_score_publish_lock",
        label="70 altı yayın kilidi aktif",
        value_type="bool",
        default=True,
        description="70 altı karne Başkan/Üst Onay tamamlanmadan personele yayınlanamaz.",
    ),
    Phase1RuleSetting(
        full_key=SETTING_STATUS_LANGUAGE_MODE,
        module_key="performance_flow",
        setting_key="status_language_mode",
        label="Statü dili",
        value_type="string",
        default="institutional_tr",
        description="Teknik statü kodlarının kullanıcıya kurumsal Türkçe gösterilmesini sağlar.",
    ),
    Phase1RuleSetting(
        full_key=SETTING_PUBLISH_PREFLIGHT_USES_RULE_CENTER,
        module_key="performance_flow",
        setting_key="publish_preflight_uses_rule_center",
        label="Yayın ön kontrol kural merkezini kullansın",
        value_type="bool",
        default=True,
        description="Yayın öncesi kontrolün merkezi performans kural motorundan beslenmesini zorunlu tutar.",
    ),
    Phase1RuleSetting(
        full_key=SETTING_PERSONNEL_SUPPORT_PREAPPROVAL_REQUIRED,
        module_key="performance_flow",
        setting_key="personnel_support_publish_preapproval_required",
        label="Yayın öncesi Personel ve Destek ön onayı zorunlu",
        value_type="bool",
        default=True,
        description="Nihai yayın öncesinde Personel ve Destek Hizmetleri Grup Başkanı ön onay adımını açık tutar.",
    ),
)

PHASE1_RULE_SETTING_BY_FULL_KEY = {item.full_key: item for item in PHASE1_RULE_SETTINGS}
PHASE1_RULE_SETTING_BY_MODULE_KEY = {(item.module_key, item.setting_key): item for item in PHASE1_RULE_SETTINGS}


@dataclass(frozen=True)
class Phase1RuleDecision:
    requires_score_comment: bool
    requires_general_comment: bool
    requires_president_approval: bool
    publish_locked: bool
    display_status: str
    reviewer_action_type: str = "score"
    reviewer_action_label: str = "Puanlama Bekliyor"
    affects_score: bool = True
    reasons: tuple[str, ...] = ()
    version: str = PHASE1_RULE_CENTER_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "requires_score_comment": self.requires_score_comment,
            "requires_general_comment": self.requires_general_comment,
            "requires_president_approval": self.requires_president_approval,
            "publish_locked": self.publish_locked,
            "display_status": self.display_status,
            "reviewer_action_type": self.reviewer_action_type,
            "reviewer_action_label": self.reviewer_action_label,
            "affects_score": self.affects_score,
            "reasons": list(self.reasons),
            "version": self.version,
        }


@dataclass(frozen=True)
class Phase1RuleContext:
    criteria_score: Any = None
    final_score: Any = None
    status_code: Any = None
    president_approved: bool = False
    reviewer_level: Any = None
    third_reviewer_mode: Any = None
    settings: Mapping[str, Any] | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "on", "yes", "evet", "aktif", "enabled"}


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None


def _normalize_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _coerce_setting_value(value: Any, value_type: str, default: Any) -> Any:
    if value_type == "bool":
        return _coerce_bool(value, bool(default))
    if value_type == "int":
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return default
    if value_type == "float":
        parsed = _coerce_float(value)
        return default if parsed is None else parsed
    text = _normalize_text(value)
    return text if text else default


def default_phase1_rule_settings() -> dict[str, Any]:
    return {item.full_key: item.default for item in PHASE1_RULE_SETTINGS}


def catalog_rows_for_gate() -> list[dict[str, Any]]:
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
        for item in PHASE1_RULE_SETTINGS
    ]


def get_phase1_rule_setting(full_key: str, default: Any | None = None) -> Any:
    definition = PHASE1_RULE_SETTING_BY_FULL_KEY.get(full_key)
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


def get_phase1_rule_settings(overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    values = default_phase1_rule_settings()
    for item in PHASE1_RULE_SETTINGS:
        values[item.full_key] = get_phase1_rule_setting(item.full_key, item.default)
    if overrides:
        values.update(dict(overrides))
    return values


def is_score_comment_required(score: Any, settings: Mapping[str, Any] | None = None) -> bool:
    values = get_phase1_rule_settings(settings)
    score_value = _coerce_float(score)
    if score_value is None:
        return False
    if int(score_value) == MIN_CRITERIA_SCORE:
        return _coerce_bool(values.get(SETTING_REQUIRE_COMMENT_FOR_SCORE_1), True)
    if int(score_value) == MAX_CRITERIA_SCORE:
        return _coerce_bool(values.get(SETTING_REQUIRE_COMMENT_FOR_SCORE_5), True)
    return False


def is_general_comment_required(final_score: Any, settings: Mapping[str, Any] | None = None) -> bool:
    values = get_phase1_rule_settings(settings)
    score_value = _coerce_float(final_score)
    if score_value is None:
        return False
    if score_value < LOW_SCORE_THRESHOLD:
        return _coerce_bool(values.get(SETTING_REQUIRE_GENERAL_COMMENT_BELOW_70), True)
    if score_value > HIGH_SCORE_THRESHOLD:
        return _coerce_bool(values.get(SETTING_REQUIRE_GENERAL_COMMENT_ABOVE_90), True)
    return False


def requires_president_approval(final_score: Any, settings: Mapping[str, Any] | None = None) -> bool:
    values = get_phase1_rule_settings(settings)
    score_value = _coerce_float(final_score)
    if score_value is None:
        return False
    return score_value < LOW_SCORE_THRESHOLD and _coerce_bool(
        values.get(SETTING_LOW_SCORE_REQUIRES_PRESIDENT_APPROVAL), True
    )


def is_publish_locked(final_score: Any, president_approved: bool = False, settings: Mapping[str, Any] | None = None) -> bool:
    values = get_phase1_rule_settings(settings)
    score_value = _coerce_float(final_score)
    if score_value is None or score_value >= LOW_SCORE_THRESHOLD:
        return False
    if president_approved:
        return False
    return _coerce_bool(values.get(SETTING_LOW_SCORE_PUBLISH_LOCK), True)


def display_status(status_code: Any, settings: Mapping[str, Any] | None = None) -> str:
    values = get_phase1_rule_settings(settings)
    language_mode = _normalize_text(values.get(SETTING_STATUS_LANGUAGE_MODE) or "institutional_tr")
    code = _normalize_text(status_code)
    if not code:
        return TECHNICAL_STATUS_FALLBACK_LABEL
    if language_mode != "institutional_tr":
        return INSTITUTIONAL_TR_STATUS_LABELS.get(code, TECHNICAL_STATUS_FALLBACK_LABEL)
    return INSTITUTIONAL_TR_STATUS_LABELS.get(code, TECHNICAL_STATUS_FALLBACK_LABEL)


def reviewer_action_decision(reviewer_level: Any = None, third_reviewer_mode: Any = None) -> dict[str, Any]:
    try:
        level = int(str(reviewer_level or "").strip())
    except ValueError:
        level = 0
    mode = _normalize_text(third_reviewer_mode).lower()
    if level == 3 and mode in {"comment", "comment_only", "yorum", "yorumcu", "view_only"}:
        return {"action_type": "comment", "label": "Yorum/Görüş Bekliyor", "affects_score": False}
    return {"action_type": "score", "label": "Puanlama Bekliyor", "affects_score": True}


def evaluate_phase1_rules(context: Phase1RuleContext | Mapping[str, Any] | None = None) -> Phase1RuleDecision:
    if context is None:
        ctx = Phase1RuleContext()
    elif isinstance(context, Phase1RuleContext):
        ctx = context
    else:
        ctx = Phase1RuleContext(
            criteria_score=context.get("criteria_score"),
            final_score=context.get("final_score"),
            status_code=context.get("status_code"),
            president_approved=_coerce_bool(context.get("president_approved"), False),
            reviewer_level=context.get("reviewer_level"),
            third_reviewer_mode=context.get("third_reviewer_mode"),
            settings=context.get("settings"),
            extra={k: v for k, v in context.items() if k not in {
                "criteria_score",
                "final_score",
                "status_code",
                "president_approved",
                "reviewer_level",
                "third_reviewer_mode",
                "settings",
            }},
        )

    settings = get_phase1_rule_settings(ctx.settings)
    score_comment = is_score_comment_required(ctx.criteria_score, settings)
    general_comment = is_general_comment_required(ctx.final_score, settings)
    president_required = requires_president_approval(ctx.final_score, settings)
    publish_lock = is_publish_locked(ctx.final_score, ctx.president_approved, settings)
    reviewer = reviewer_action_decision(ctx.reviewer_level, ctx.third_reviewer_mode)

    reasons: list[str] = []
    if score_comment:
        reasons.append("Kriter puanı için açıklama zorunlu.")
    if general_comment:
        reasons.append("Nihai puan eşiği nedeniyle ayrıntılı genel görüş zorunlu.")
    if president_required:
        reasons.append("70 altı sonuç Başkan/Üst Onay gerektirir.")
    if publish_lock:
        reasons.append("Başkan/Üst Onay tamamlanmadan karne personele yayımlanamaz.")

    return Phase1RuleDecision(
        requires_score_comment=score_comment,
        requires_general_comment=general_comment,
        requires_president_approval=president_required,
        publish_locked=publish_lock,
        display_status=display_status(ctx.status_code, settings),
        reviewer_action_type=str(reviewer["action_type"]),
        reviewer_action_label=str(reviewer["label"]),
        affects_score=bool(reviewer["affects_score"]),
        reasons=tuple(reasons),
    )


def build_status_choice_list(codes: list[str] | tuple[str, ...] | None = None) -> list[dict[str, str]]:
    source_codes = codes or tuple(INSTITUTIONAL_TR_STATUS_LABELS.keys())
    return [{"value": code, "label": display_status(code)} for code in source_codes]


def seed_phase1_rule_settings(*, commit: bool = True) -> dict[str, int]:
    """Eksik Faz 1 ayarlarını module_settings tablosuna ekler.

    Uygulama/DB baglami yoksa hata firlatmak yerine skipped doner. Repair script
    bu fonksiyonu kullanir; migration da ayni sozlesmedeki varsayilanlari SQL ile ekler.
    """
    try:
        from app.models import ModuleSetting
        from app.models.base import db
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return {"created": 0, "updated": 0, "existing": 0, "skipped": 1}

    created = 0
    updated = 0
    existing = 0
    for item in PHASE1_RULE_SETTINGS:
        try:
            row = ModuleSetting.query.filter_by(module_key=item.module_key, setting_key=item.setting_key).first()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return {"created": created, "updated": updated, "existing": existing, "skipped": 1}
        if row is None:
            row = ModuleSetting(
                module_key=item.module_key,
                setting_key=item.setting_key,
                label=item.label,
                value_text=str(item.default),
                value_type=item.value_type,
                description=item.description,
                is_active=True,
            )
            db.session.add(row)
            created += 1
        else:
            changed = False
            if not getattr(row, "label", None):
                row.label = item.label
                changed = True
            if not getattr(row, "value_type", None):
                row.value_type = item.value_type
                changed = True
            if getattr(row, "value_text", None) in (None, ""):
                row.value_text = str(item.default)
                changed = True
            if not getattr(row, "description", None):
                row.description = item.description
                changed = True
            if changed:
                updated += 1
            else:
                existing += 1
    if commit:
        try:
            db.session.commit()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            db.session.rollback()
            return {"created": created, "updated": updated, "existing": existing, "skipped": 1}
    return {"created": created, "updated": updated, "existing": existing, "skipped": 0}


__all__ = [
    "HIGH_SCORE_THRESHOLD",
    "INSTITUTIONAL_TR_STATUS_LABELS",
    "LOW_SCORE_THRESHOLD",
    "MAX_CRITERIA_SCORE",
    "MIN_CRITERIA_SCORE",
    "PHASE1_RULE_CENTER_VERSION",
    "PHASE1_RULE_SETTINGS",
    "PHASE1_RULE_SETTING_BY_FULL_KEY",
    "PHASE1_RULE_SETTING_BY_MODULE_KEY",
    "Phase1RuleContext",
    "Phase1RuleDecision",
    "Phase1RuleSetting",
    "SETTING_LOW_SCORE_PUBLISH_LOCK",
    "SETTING_LOW_SCORE_REQUIRES_PRESIDENT_APPROVAL",
    "SETTING_PERSONNEL_SUPPORT_PREAPPROVAL_REQUIRED",
    "SETTING_PUBLISH_PREFLIGHT_USES_RULE_CENTER",
    "SETTING_REQUIRE_COMMENT_FOR_SCORE_1",
    "SETTING_REQUIRE_COMMENT_FOR_SCORE_5",
    "SETTING_REQUIRE_GENERAL_COMMENT_ABOVE_90",
    "SETTING_REQUIRE_GENERAL_COMMENT_BELOW_70",
    "SETTING_STATUS_LANGUAGE_MODE",
    "TECHNICAL_STATUS_CODES_BLOCKED_FROM_UI",
    "TECHNICAL_STATUS_FALLBACK_LABEL",
    "build_status_choice_list",
    "catalog_rows_for_gate",
    "default_phase1_rule_settings",
    "display_status",
    "evaluate_phase1_rules",
    "get_phase1_rule_setting",
    "get_phase1_rule_settings",
    "is_general_comment_required",
    "is_publish_locked",
    "is_score_comment_required",
    "requires_president_approval",
    "reviewer_action_decision",
    "seed_phase1_rule_settings",
]

# BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_BOUND
# Karne/puanlama ekranları phase5_scorecard_ui_policy sözleşmesini kullanır.
