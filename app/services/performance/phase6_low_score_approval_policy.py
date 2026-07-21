"""
BYS360 Performans Tamamlama Faz 6
Başkan/Üst Onayları ve Düşük Performans Süreci Politika Merkezi

Amaç:
- 70 altı sonuç doğrudan kesinleşmesin.
- Başkan/Üst Onay olmadan karne personele yayınlanmasın.
- Sahte Başkan onayı kaydı üretilmesin.
- Aynı takvim yılında ilk/ikinci düşük performans ayrımı kurulsun.
- Teknik statüler yerine kurumsal Türkçe ifadeler kullanılsın.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


PHASE6_POLICY_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_APPROVAL_POLICY"

LOW_SCORE_THRESHOLD = 70.0

STATUS_LABELS = {
    "not_required": "Üst Onay Gerekmiyor",
    "president_pending": "Başkan/Üst Onay Bekliyor",
    "blocked_president_pending": "Başkan/Üst Onay Yayın Kilidi",
    "approved_by_president": "Başkan/Üst Onay Tamamlandı",
    "rejected_by_president": "Başkan/Üst Onay İade Edildi",
    "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
    "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
    "process_record_required": "Personel Süreç Kaydı Bekliyor",
    "publish_allowed": "Yayınlanabilir",
}

PROCESS_STEPS = [
    "Değerlendirme tamamlandı",
    "70 altı sonuç tespit edildi",
    "Başkan/Üst Onay sürecine alındı",
    "Onay tamamlandı",
    "Personel süreç kaydı oluşturuldu",
    "Yayın sürecine hazırlandı",
]


@dataclass(frozen=True)
class LowScoreDecision:
    low_score: bool
    approval_required: bool
    approval_status: str
    approval_label: str
    publish_blocked: bool
    publish_lock_label: str
    process_record_required: bool
    warning_level: str
    warning_label: str
    can_publish: bool
    next_action: str


def _float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "evet", "on", "aktif", "enabled"}


def status_label(status: Any) -> str:
    raw = str(status or "").strip()
    if not raw:
        return "Süreç Durumu"
    normalized = raw.lower().replace(" ", "_").replace("-", "_")
    return STATUS_LABELS.get(normalized, raw)


def is_low_score(score: Any, threshold: float = LOW_SCORE_THRESHOLD) -> bool:
    numeric = _float(score)
    if numeric is None:
        return False
    return numeric < threshold


def classify_low_score_repeat(previous_low_count_in_year: Any = 0) -> tuple[str, str]:
    try:
        count = int(previous_low_count_in_year or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        count = 0

    if count <= 0:
        return "first_low_warning", STATUS_LABELS["first_low_warning"]
    return "second_low_repeat", STATUS_LABELS["second_low_repeat"]


def resolve_low_score_approval(
    *,
    final_score: Any,
    approval_status: Any = None,
    process_record_exists: bool = False,
    previous_low_count_in_year: Any = 0,
    settings: Mapping[str, Any] | None = None,
) -> LowScoreDecision:
    settings = settings or {}
    threshold = _float(settings.get("performance.phase6.low_score_threshold"), LOW_SCORE_THRESHOLD) or LOW_SCORE_THRESHOLD
    approval_enabled = _bool(settings.get("performance.phase6.low_score_requires_upper_approval", True), True)

    low = is_low_score(final_score, threshold=threshold)
    if not low or not approval_enabled:
        return LowScoreDecision(
            low_score=low,
            approval_required=False,
            approval_status="not_required",
            approval_label=STATUS_LABELS["not_required"],
            publish_blocked=False,
            publish_lock_label=STATUS_LABELS["publish_allowed"],
            process_record_required=False,
            warning_level="not_required",
            warning_label="Uyarı Süreci Gerekmiyor",
            can_publish=True,
            next_action="Yayın süreci normal akışta ilerleyebilir.",
        )

    normalized_status = str(approval_status or "president_pending").strip().lower().replace(" ", "_").replace("-", "_")
    approved = normalized_status in {"approved_by_president", "approved", "upper_approved", "president_approved"}
    rejected = normalized_status in {"rejected_by_president", "rejected", "returned", "president_rejected"}
    warning_key, warning_label = classify_low_score_repeat(previous_low_count_in_year)

    if rejected:
        return LowScoreDecision(
            low_score=True,
            approval_required=True,
            approval_status="rejected_by_president",
            approval_label=STATUS_LABELS["rejected_by_president"],
            publish_blocked=True,
            publish_lock_label=STATUS_LABELS["blocked_president_pending"],
            process_record_required=True,
            warning_level=warning_key,
            warning_label=warning_label,
            can_publish=False,
            next_action="İade gerekçesi değerlendirilerek süreç yeniden hazırlanmalıdır.",
        )

    if not approved:
        return LowScoreDecision(
            low_score=True,
            approval_required=True,
            approval_status="president_pending",
            approval_label=STATUS_LABELS["president_pending"],
            publish_blocked=True,
            publish_lock_label=STATUS_LABELS["blocked_president_pending"],
            process_record_required=True,
            warning_level=warning_key,
            warning_label=warning_label,
            can_publish=False,
            next_action="Başkan/Üst Onay tamamlanmadan karne personele yayınlanamaz.",
        )

    if not process_record_exists:
        return LowScoreDecision(
            low_score=True,
            approval_required=True,
            approval_status="approved_by_president",
            approval_label=STATUS_LABELS["approved_by_president"],
            publish_blocked=True,
            publish_lock_label=STATUS_LABELS["process_record_required"],
            process_record_required=True,
            warning_level=warning_key,
            warning_label=warning_label,
            can_publish=False,
            next_action="Onay sonrası personel süreç kaydı oluşturulmalıdır.",
        )

    return LowScoreDecision(
        low_score=True,
        approval_required=True,
        approval_status="approved_by_president",
        approval_label=STATUS_LABELS["approved_by_president"],
        publish_blocked=False,
        publish_lock_label=STATUS_LABELS["publish_allowed"],
        process_record_required=False,
        warning_level=warning_key,
        warning_label=warning_label,
        can_publish=True,
        next_action="Yayın öncesi kurumsal kontrol adımına geçilebilir.",
    )


def should_create_president_approval_record(final_score: Any, existing_record: bool = False) -> bool:
    """
    Sahte onay kaydı üretimini engeller.
    Yalnızca gerçek 70 altı nihai puan varsa ve kayıt yoksa onay kaydı üretilebilir.
    """
    return is_low_score(final_score) and not bool(existing_record)


def filter_real_low_score_approvals(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """
    Başkan Onayları ekranına yalnızca gerçek düşük performans kayıtlarını taşır.
    """
    clean: list[dict[str, Any]] = []
    for row in rows or []:
        final_score = row.get("final_score") or row.get("score") or row.get("nihai_puan")
        if not is_low_score(final_score):
            continue
        item = dict(row)
        item["approval_label"] = status_label(item.get("approval_status") or "president_pending")
        item["publish_lock_label"] = STATUS_LABELS["blocked_president_pending"]
        clean.append(item)
    return clean


def build_low_score_process_steps(decision: LowScoreDecision) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for index, title in enumerate(PROCESS_STEPS, start=1):
        state = "pending"
        if index == 1:
            state = "done"
        elif index == 2 and decision.low_score:
            state = "done"
        elif index == 3 and decision.approval_required:
            state = "done" if decision.approval_status != "president_pending" else "active"
        elif index == 4 and decision.approval_status == "approved_by_president":
            state = "done"
        elif index == 5 and not decision.process_record_required and decision.approval_status == "approved_by_president":
            state = "done"
        elif index == 6 and decision.can_publish:
            state = "done"

        steps.append(
            {
                "order": index,
                "title": title,
                "state": state,
                "label": {
                    "done": "Tamamlandı",
                    "active": "Devam Ediyor",
                    "pending": "Bekliyor",
                }.get(state, "Bekliyor"),
            }
        )
    return steps


def phase6_approval_contract() -> dict[str, Any]:
    return {
        "low_score_threshold": LOW_SCORE_THRESHOLD,
        "low_score_requires_upper_approval": True,
        "publish_block_until_approval": True,
        "process_record_required_after_approval": True,
        "fake_approval_records_forbidden": True,
        "first_second_low_score_tracking": True,
        "president_approval_card_detail_required": True,
        "technical_status_hidden": True,
        "phase_marker": PHASE6_POLICY_MARKER,
    }
