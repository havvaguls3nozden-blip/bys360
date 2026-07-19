from __future__ import annotations

import logging

"""BYS360 AI Karar Destek Faz 6 düşük performans onay politikası.

Bu servis 70 altı performans sonuçlarının Başkan/Üst Onay ve yayın kilidi
mantığıyla güvenli şekilde yorumlanması için kullanılır. Karar üretmez; yalnızca
yetkili kullanıcıların görmesi gereken süreç sinyallerini kurumsal Türkçe ile
hazırlar.

BYS360_AI_DECISION_FAZ6_LOW_PERFORMANCE_POLICY
"""

from dataclasses import dataclass
from typing import Any, Mapping

logger = logging.getLogger(__name__)


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "evet", "yes", "on", "aktif"}:
        return True
    if text in {"0", "false", "hayir", "hayır", "no", "off", "pasif"}:
        return False
    return default


def _to_float(value: Any, default: float) -> float:
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def score_to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(str(value).replace(",", "."))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def safe_attr(obj: Any, *names: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        for name in names:
            if name in obj:
                return obj[name]
        return default
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def display_score(value: Any) -> str:
    numeric = score_to_float(value)
    if numeric is None:
        return "—"
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.2f}".rstrip("0").rstrip(".")


_STATUS_LABELS = {
    "president_pending": "Başkan/Üst Onay Bekliyor",
    "blocked_president_pending": "Başkan/Üst Onay Yayın Kilidi",
    "upper_approval_pending": "Başkan/Üst Onay Bekliyor",
    "approved_by_president": "Başkan/Üst Onay Tamamlandı",
    "rejected_by_president": "Başkan/Üst Onay İade Edildi",
    "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
    "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
    "published": "Personele Yayınlandı",
    "completed": "Değerlendirme Tamamlandı",
    "pending": "İşlem Bekliyor",
    "returned": "İade Edildi",
    "cancelled": "İptal Edildi",
}


def normalize_process_label(value: Any, fallback: str = "Süreç Kontrolü Bekliyor") -> str:
    if value is None or value == "":
        return fallback
    text = str(value).strip()
    key = text.lower()
    if key in _STATUS_LABELS:
        return _STATUS_LABELS[key]
    cleaned = text.replace("_", " ").replace("-", " ").strip()
    lowered = cleaned.lower()
    if lowered in _STATUS_LABELS:
        return _STATUS_LABELS[lowered]
    if cleaned:
        return cleaned[:1].upper() + cleaned[1:]
    return fallback


@dataclass(frozen=True)
class LowPerformanceApprovalPolicy:
    low_score_limit: float = 70.0
    high_score_limit: float = 90.0
    direct_upper_approval: bool = True
    require_low_score_general_comment: bool = True
    lock_publish_until_upper_approval: bool = True
    create_first_low_warning: bool = True
    create_repeat_low_process: bool = True
    hr_admin_observer_mode: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "low_score_limit": self.low_score_limit,
            "high_score_limit": self.high_score_limit,
            "direct_upper_approval": self.direct_upper_approval,
            "require_low_score_general_comment": self.require_low_score_general_comment,
            "lock_publish_until_upper_approval": self.lock_publish_until_upper_approval,
            "create_first_low_warning": self.create_first_low_warning,
            "create_repeat_low_process": self.create_repeat_low_process,
            "hr_admin_observer_mode": self.hr_admin_observer_mode,
        }


def build_low_performance_policy(settings: Mapping[str, Any] | None = None) -> LowPerformanceApprovalPolicy:
    data = settings or {}
    return LowPerformanceApprovalPolicy(
        low_score_limit=_to_float(
            data.get("ai_decision.faz6_low_score_limit")
            or data.get("performance.low_score_limit")
            or data.get("performance_flow.low_score_limit"),
            70.0,
        ),
        high_score_limit=_to_float(
            data.get("ai_decision.faz6_high_score_limit")
            or data.get("performance.high_score_limit"),
            90.0,
        ),
        direct_upper_approval=_to_bool(
            data.get("ai_decision.faz6_direct_upper_approval")
            or data.get("performance_flow.low_score_direct_president_approval"),
            True,
        ),
        require_low_score_general_comment=_to_bool(
            data.get("ai_decision.faz6_require_low_score_general_comment")
            or data.get("performance_flow.require_general_comment_below_70")
            or data.get("performance.require_general_comment_below_70"),
            True,
        ),
        lock_publish_until_upper_approval=_to_bool(
            data.get("ai_decision.faz6_publish_lock_until_upper_approval")
            or data.get("performance_flow.low_score_publish_lock"),
            True,
        ),
        create_first_low_warning=_to_bool(data.get("ai_decision.faz6_create_first_low_warning"), True),
        create_repeat_low_process=_to_bool(data.get("ai_decision.faz6_create_repeat_low_process"), True),
        hr_admin_observer_mode=_to_bool(data.get("ai_decision.faz6_hr_admin_observer_mode"), True),
    )


def score_requires_upper_approval(score: Any, policy: LowPerformanceApprovalPolicy | None = None) -> bool:
    p = policy or LowPerformanceApprovalPolicy()
    numeric = score_to_float(score)
    return numeric is not None and numeric < p.low_score_limit


def low_score_level(prior_low_count_same_year: int) -> dict[str, str]:
    try:
        count = max(int(prior_low_count_same_year), 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        count = 0
    if count <= 0:
        return {
            "key": "first_low_score",
            "label": "İlk Düşük Performans Kaydı",
            "action": "Düşük performans uyarısı oluşturulmalı ve personel geçmişine işlenmelidir.",
        }
    return {
        "key": "repeat_low_score",
        "label": "Tekrarlayan Düşük Performans Süreci",
        "action": "İdari süreç başlatma değerlendirmesi için yetkili onay akışı oluşturulmalıdır.",
    }
