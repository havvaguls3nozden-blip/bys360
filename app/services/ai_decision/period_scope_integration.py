
"""BYS360 AI Karar Destek Faz 8 dönem/kapsam entegrasyonu.

Performans dönemleri, kapsam tipi, kategori/grup veya seçili personel yapısını
karar destek özetine dönüştürür. Kişi detayı varsayılan olarak açılmaz; çıktı
özellikle görev üretimi, kapsam ve çakışma kontrolüne odaklanır.

BYS360_AI_DECISION_FAZ8_PERIOD_SCOPE_INTEGRATION
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from .period_scope_policy import (
    build_period_decision,
    build_period_scope_policy,
    count_overlaps,
    normalize_period,
    safe_attr,
    summarize_periods,
    to_int,
)


def _row_mapping(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if isinstance(row, Mapping):
        return dict(row)
    return {}


def _period_id(row: Any) -> Any:
    return safe_attr(row, "id", "period_id", default=None)


def assignment_count_map(assignments: Iterable[Any]) -> dict[Any, int]:
    counts: dict[Any, int] = defaultdict(int)
    for row in assignments:
        pid = safe_attr(row, "period_id", "performance_period_id", "donem_id", default=None)
        if pid is not None:
            counts[pid] += 1
    return counts


def build_period_scope_summary_payload(
    periods: Iterable[Any],
    assignments: Iterable[Any] | None = None,
    current_user: Any | None = None,
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Dönem/kapsam karar destek özetini üretir."""

    policy = build_period_scope_policy(settings)
    periods_list = list(periods)
    assignment_counts = assignment_count_map(assignments or [])
    decisions = []
    for period in periods_list:
        pid = _period_id(period)
        overlaps = count_overlaps(period, periods_list)
        decisions.append(
            build_period_decision(
                period,
                policy=policy,
                assignment_count=assignment_counts.get(pid, 0),
                overlap_count=overlaps,
            )
        )
    summary = summarize_periods(decisions)
    attention_periods = [item for item in decisions if item.get("attention_count", 0) > 0]
    return {
        "ok": True,
        "module": "AI Karar Destek Merkezi",
        "scope": "Çoklu ve Özel Dönem Yönetimi",
        "summary": summary,
        "periods": decisions,
        "attention_periods": attention_periods,
        "privacy_note": "Bu özet kişi detayı açmadan dönem, kapsam ve görev üretimi sinyali verir.",
        "safety_note": "Bu çıktı idari karar değildir; dönem hazırlığı için insan denetimli karar desteği sağlar.",
        "marker": "BYS360_AI_DECISION_FAZ8_PERIOD_SCOPE_SUMMARY_PAYLOAD",
    }


def build_single_period_payload(
    period: Any,
    all_periods: Iterable[Any] | None = None,
    assignments: Iterable[Any] | None = None,
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    policy = build_period_scope_policy(settings)
    all_periods = list(all_periods or [period])
    counts = assignment_count_map(assignments or [])
    pid = _period_id(period)
    decision = build_period_decision(
        period,
        policy=policy,
        assignment_count=counts.get(pid, 0),
        overlap_count=count_overlaps(period, all_periods),
    )
    return {
        "ok": True,
        "module": "AI Karar Destek Merkezi",
        "scope": "Dönem Kapsam Kontrolü",
        "period": decision,
        "next_step": "Dikkat maddesi varsa dönem yayına alınmadan önce kapsam ve görev üretimi kontrol edilmelidir.",
        "marker": "BYS360_AI_DECISION_FAZ8_SINGLE_PERIOD_PAYLOAD",
    }


def build_scope_preview_payload(period: Any, candidate_rows: Iterable[Any], settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Kişi adı açmadan kapsam önizleme özeti üretir."""

    policy = build_period_scope_policy(settings)
    normalized = normalize_period(period)
    category_counts: dict[str, int] = defaultdict(int)
    unit_counts: dict[str, int] = defaultdict(int)
    total = 0
    for row in candidate_rows:
        total += 1
        category = safe_attr(row, "category_name", "personnel_category", "category", default="Kategori Belirtilmemiş") or "Kategori Belirtilmemiş"
        unit = safe_attr(row, "unit_name", "organization_unit_name", "birim", default="Birim Belirtilmemiş") or "Birim Belirtilmemiş"
        category_counts[str(category)] += 1
        unit_counts[str(unit)] += 1
    warnings = []
    if total == 0:
        warnings.append("Seçilen kapsama uygun personel bulunamadı.")
    if normalized["scope_type"] in {"selected_personnel", "personnel"} and total > policy.selected_personnel_limit:
        warnings.append("Seçili personel kapsamı beklenenden geniş görünüyor.")
    return {
        "ok": True,
        "module": "AI Karar Destek Merkezi",
        "scope": "Kapsam Önizleme",
        "period": normalized,
        "candidate_count": total,
        "category_distribution": dict(category_counts),
        "unit_distribution": dict(unit_counts),
        "attention_items": warnings,
        "privacy_note": "Önizleme kişi adı ve puan detayı göstermez; yalnızca sayısal kapsam özeti verir.",
        "marker": "BYS360_AI_DECISION_FAZ8_SCOPE_PREVIEW_PAYLOAD",
    }
