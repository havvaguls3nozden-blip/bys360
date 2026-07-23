from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

"""BYS360 Performans Faz 1.3 - merkezi performans kural motoru.

Bu servis Faz 1.2'de tanımlanan ``performance.*`` ayarlarını okuyarak
performans değerlendirme kurallarını tek merkezden yorumlar.

Faz 1.3 bilinçli olarak route/template davranışını doğrudan değiştirmez.
Faz 1.4'te yayın öncesi kontrol ve ekranlar bu servise bağlanacaktır.
"""

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

THIRD_REVIEWER_MODE_COMMENT = "comment"
THIRD_REVIEWER_MODE_SCORE = "score"

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
    "president_pending": "Başkan Onayı Bekliyor",
    "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
    "hr_precheck": "İK/Admin Ön Kontrolünde",
    "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
    "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
    "approved_by_president": "Başkan Tarafından Onaylandı",
    "rejected_by_president": "Başkan Tarafından İade Edildi",
    "publish_locked": "Yayın Kilidi Aktif",
    "publish_ready": "Yayına Hazır",
    "published_to_employee": "Personele Yayımlandı",
    "comment_pending": "Yorum/Görüş Bekliyor",
    "score_pending": "Puanlama Bekliyor",
}

TECHNICAL_STATUS_FALLBACK_LABEL = "Süreç Durumu Belirleniyor"


@dataclass(frozen=True)
class PerformanceRuleContext:
    """Kural motoruna gönderilen tek değerlendirme bağlamı."""

    criteria_score: int | float | None = None
    final_score: int | float | None = None
    status_code: str | None = None
    president_approved: bool = False
    third_reviewer_mode: str | None = None
    settings: Mapping[str, Any] | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PerformanceRuleDecision:
    """Kural motorunun route/template katmanına döndüğü sade karar nesnesi."""

    requires_score_comment: bool
    requires_general_comment: bool
    requires_president_approval: bool
    publish_locked: bool
    display_status: str
    reviewer_action_type: str
    reviewer_action_label: str
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewerActionDecision:
    action_type: str
    label: str
    affects_score: bool


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


def _normalize_status_code(status_code: Any) -> str:
    return "" if status_code is None else str(status_code).strip()


def _normalize_third_reviewer_mode(mode: Any) -> str:
    text = "" if mode is None else str(mode).strip().lower()
    if text in {"score", "puan", "puan_modu", "scoring", "weighted"}:
        return THIRD_REVIEWER_MODE_SCORE
    return THIRD_REVIEWER_MODE_COMMENT


def load_performance_rule_settings(overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Faz 1.2 ayarlarını okur ve istenirse test/çağrı bazlı override uygular."""
    try:
        from app.services.performance.performance_rule_settings import get_performance_rule_settings

        settings = dict(get_performance_rule_settings())
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        settings = {
            SETTING_REQUIRE_COMMENT_FOR_SCORE_1: True,
            SETTING_REQUIRE_COMMENT_FOR_SCORE_5: True,
            SETTING_REQUIRE_GENERAL_COMMENT_BELOW_70: True,
            SETTING_REQUIRE_GENERAL_COMMENT_ABOVE_90: True,
            SETTING_LOW_SCORE_REQUIRES_PRESIDENT_APPROVAL: True,
            SETTING_LOW_SCORE_PUBLISH_LOCK: True,
            SETTING_STATUS_LANGUAGE_MODE: "institutional_tr",
        }

    if overrides:
        settings.update(dict(overrides))
    return settings


def is_score_comment_required(score: Any, settings: Mapping[str, Any] | None = None) -> bool:
    """1 veya 5 kriter puanında açıklama zorunluluğu kararını döndürür."""
    values = load_performance_rule_settings(settings)
    score_value = _coerce_float(score)
    if score_value is None:
        return False

    if int(score_value) == MIN_CRITERIA_SCORE:
        return _coerce_bool(values.get(SETTING_REQUIRE_COMMENT_FOR_SCORE_1), True)
    if int(score_value) == MAX_CRITERIA_SCORE:
        return _coerce_bool(values.get(SETTING_REQUIRE_COMMENT_FOR_SCORE_5), True)
    return False


def is_general_comment_required(final_score: Any, settings: Mapping[str, Any] | None = None) -> bool:
    """70 altı veya 90 üstü nihai sonuçta genel görüş zorunluluğunu döndürür."""
    values = load_performance_rule_settings(settings)
    score_value = _coerce_float(final_score)
    if score_value is None:
        return False

    if score_value < LOW_SCORE_THRESHOLD:
        return _coerce_bool(values.get(SETTING_REQUIRE_GENERAL_COMMENT_BELOW_70), True)
    if score_value > HIGH_SCORE_THRESHOLD:
        return _coerce_bool(values.get(SETTING_REQUIRE_GENERAL_COMMENT_ABOVE_90), True)
    return False


def requires_president_approval(final_score: Any, settings: Mapping[str, Any] | None = None) -> bool:
    """70 altı sonuç için Başkan onayı gerekip gerekmediğini döndürür."""
    values = load_performance_rule_settings(settings)
    score_value = _coerce_float(final_score)
    if score_value is None:
        return False
    return score_value < LOW_SCORE_THRESHOLD and _coerce_bool(
        values.get(SETTING_LOW_SCORE_REQUIRES_PRESIDENT_APPROVAL), True
    )


def is_publish_locked(
    final_score: Any,
    president_approved: bool = False,
    settings: Mapping[str, Any] | None = None,
) -> bool:
    """70 altı karne için yayın kilidi kararını döndürür."""
    values = load_performance_rule_settings(settings)
    score_value = _coerce_float(final_score)
    if score_value is None:
        return False
    if score_value >= LOW_SCORE_THRESHOLD:
        return False
    if president_approved:
        return False
    return _coerce_bool(values.get(SETTING_LOW_SCORE_PUBLISH_LOCK), True)


def display_status(status_code: Any, settings: Mapping[str, Any] | None = None) -> str:
    """Teknik statü kodunu kullanıcıya gösterilecek Türkçe ifadeye çevirir."""
    values = load_performance_rule_settings(settings)
    language_mode = str(values.get(SETTING_STATUS_LANGUAGE_MODE) or "institutional_tr").strip()
    code = _normalize_status_code(status_code)

    if not code:
        return TECHNICAL_STATUS_FALLBACK_LABEL

    # Faz 1.3'te kullanıcı arayüzü için tek desteklenen mod kurumsal Türkçe.
    # Farklı değer girilse bile teknik kodu ekrana basmamak için güvenli etikete döner.
    if language_mode != "institutional_tr":
        return INSTITUTIONAL_TR_STATUS_LABELS.get(code, TECHNICAL_STATUS_FALLBACK_LABEL)

    return INSTITUTIONAL_TR_STATUS_LABELS.get(code, TECHNICAL_STATUS_FALLBACK_LABEL)


def reviewer_action_decision(
    reviewer_level: int | str | None = None,
    third_reviewer_mode: str | None = None,
) -> ReviewerActionDecision:
    """Amirin puan mı yorum/görüş mü gireceğini belirler.

    3. amir yorum modundaysa puan bekleme dili kullanılmaz. Diğer seviyelerde
    varsayılan işlem puanlamadır.
    """
    try:
        level = int(str(reviewer_level or "").strip())
    except ValueError:
        level = 0

    if level == 3 and _normalize_third_reviewer_mode(third_reviewer_mode) == THIRD_REVIEWER_MODE_COMMENT:
        return ReviewerActionDecision(
            action_type="comment",
            label="Yorum/Görüş Bekliyor",
            affects_score=False,
        )

    return ReviewerActionDecision(
        action_type="score",
        label="Puanlama Bekliyor",
        affects_score=True,
    )


def evaluate_performance_rules(context: PerformanceRuleContext | Mapping[str, Any] | None = None) -> PerformanceRuleDecision:
    """Route/template katmanının tek çağrıyla kullanabileceği ana karar fonksiyonu."""
    if context is None:
        ctx = PerformanceRuleContext()
    elif isinstance(context, PerformanceRuleContext):
        ctx = context
    else:
        ctx = PerformanceRuleContext(
            criteria_score=context.get("criteria_score"),
            final_score=context.get("final_score"),
            status_code=context.get("status_code"),
            president_approved=_coerce_bool(context.get("president_approved"), False),
            third_reviewer_mode=context.get("third_reviewer_mode"),
            settings=context.get("settings"),
            extra={k: v for k, v in context.items() if k not in {
                "criteria_score",
                "final_score",
                "status_code",
                "president_approved",
                "third_reviewer_mode",
                "settings",
            }},
        )

    settings = load_performance_rule_settings(ctx.settings)
    score_comment_required = is_score_comment_required(ctx.criteria_score, settings)
    general_comment_required = is_general_comment_required(ctx.final_score, settings)
    president_required = requires_president_approval(ctx.final_score, settings)
    publish_lock = is_publish_locked(ctx.final_score, ctx.president_approved, settings)

    reviewer_level = ctx.extra.get("reviewer_level") if ctx.extra else None
    reviewer = reviewer_action_decision(reviewer_level, ctx.third_reviewer_mode)

    reasons: list[str] = []
    if score_comment_required:
        reasons.append("Kriter puanı için açıklama zorunlu.")
    if general_comment_required:
        reasons.append("Nihai puan eşiği nedeniyle ayrıntılı genel görüş zorunlu.")
    if president_required:
        reasons.append("70 altı sonuç Başkan onayı gerektirir.")
    if publish_lock:
        reasons.append("Başkan onayı tamamlanmadan karne personele yayımlanamaz.")

    return PerformanceRuleDecision(
        requires_score_comment=score_comment_required,
        requires_general_comment=general_comment_required,
        requires_president_approval=president_required,
        publish_locked=publish_lock,
        display_status=display_status(ctx.status_code, settings),
        reviewer_action_type=reviewer.action_type,
        reviewer_action_label=reviewer.label,
        reasons=tuple(reasons),
    )


def build_status_choice_list(codes: list[str] | tuple[str, ...] | None = None) -> list[dict[str, str]]:
    """Template/form katmanı için güvenli statü seçenekleri üretir."""
    source_codes = codes or tuple(INSTITUTIONAL_TR_STATUS_LABELS.keys())
    return [{"value": code, "label": display_status(code)} for code in source_codes]


__all__ = [
    "HIGH_SCORE_THRESHOLD",
    "INSTITUTIONAL_TR_STATUS_LABELS",
    "LOW_SCORE_THRESHOLD",
    "MAX_CRITERIA_SCORE",
    "MIN_CRITERIA_SCORE",
    "PerformanceRuleContext",
    "PerformanceRuleDecision",
    "ReviewerActionDecision",
    "build_status_choice_list",
    "display_status",
    "evaluate_performance_rules",
    "is_general_comment_required",
    "is_publish_locked",
    "is_score_comment_required",
    "load_performance_rule_settings",
    "requires_president_approval",
    "reviewer_action_decision",
]

# BYS360_PERFORMANCE_COMPLETION_PHASE1_RULE_CENTER_DELEGATION
# Bu blok, eski import yolunu kullanan kodlarin Faz 1 merkezi kural sozlesmesini
# ayni fonksiyon adlariyla kullanmasini saglar. Fonksiyonlar altta tekrar
# tanimlandigi icin Python global lookup ile mevcut route/servisler yeni merkezi okur.
try:
    from app.services.performance import phase1_rule_center as _phase1_rule_center

    def load_performance_rule_settings(overrides=None):
        return _phase1_rule_center.get_phase1_rule_settings(overrides)

    def is_score_comment_required(score, settings=None):
        return _phase1_rule_center.is_score_comment_required(score, settings)

    def is_general_comment_required(final_score, settings=None):
        return _phase1_rule_center.is_general_comment_required(final_score, settings)

    def requires_president_approval(final_score, settings=None):
        return _phase1_rule_center.requires_president_approval(final_score, settings)

    def is_publish_locked(final_score, president_approved=False, settings=None):
        return _phase1_rule_center.is_publish_locked(final_score, president_approved, settings)

    def display_status(status_code, settings=None):
        return _phase1_rule_center.display_status(status_code, settings)

    def build_status_choice_list(codes=None):
        return _phase1_rule_center.build_status_choice_list(codes)

    def reviewer_action_decision(reviewer_level=None, third_reviewer_mode=None):
        _decision = _phase1_rule_center.reviewer_action_decision(reviewer_level, third_reviewer_mode)
        try:
            return ReviewerActionDecision(
                action_type=_decision.get("action_type", "score"),
                label=_decision.get("label", "Puanlama Bekliyor"),
                affects_score=bool(_decision.get("affects_score", True)),
            )
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return _decision
except Exception:
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/performance/services/performance_rule_engine.py)")

# BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_BOUND
# 3. amir opsiyonelliği ve sahte görev temizliği phase4_third_manager_policy üzerinden izlenir.

# BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_BOUND
# Karne/puanlama ekranları phase5_scorecard_ui_policy sözleşmesini kullanır.

# BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_APPROVAL_BOUND
# 70 altı düşük performans üst onay/yayın kilidi phase6_low_score_approval_policy ile izlenir.
