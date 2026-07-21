
"""BYS360 AI Karar Destek Faz 7 geçmiş karne arşivi entegrasyonu.

Geçmiş performans kayıtlarını kişi mahremiyetini koruyarak karar destek
özetine dönüştürür. Personel kendi kayıt detayını görebilir; yönetici
ekranları varsayılan olarak kişi detayı içermeyen özet üretir.

BYS360_AI_DECISION_FAZ7_HISTORICAL_ARCHIVE_INTEGRATION
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

from .historical_archive_policy import (
    ArchivePolicy,
    build_archive_policy,
    can_view_archive_detail,
    can_view_archive_summary,
    display_score,
    risk_level_from_history,
    safe_attr,
    to_float,
    to_int,
    trend_label,
)


def _date_text(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, (date, datetime)):
        return value.strftime("%d.%m.%Y")
    text = str(value)
    if len(text) >= 10 and text[4:5] == "-":
        return f"{text[8:10]}.{text[5:7]}.{text[0:4]}"
    return text


def normalize_archive_row(row: Any, policy: ArchivePolicy | None = None, include_person: bool = False) -> dict[str, Any]:
    policy = policy or build_archive_policy()
    mapping = dict(row._mapping) if hasattr(row, "_mapping") else (dict(row) if isinstance(row, Mapping) else {})
    source = mapping or row
    score = safe_attr(source, "score_value", "score", "puan", default=None)
    period_year = to_int(safe_attr(source, "period_year", "year", "yil", "yıl", default=None))
    period_title = safe_attr(source, "period_title", "period_name", "donem", "dönem", default="Geçmiş Dönem")
    user_id = safe_attr(source, "user_id", "personnel_id", "employee_id", default=None)
    payload = {
        "id": safe_attr(source, "id", default=None),
        "user_id": user_id,
        "period_year": period_year,
        "period_title": str(period_title or "Geçmiş Dönem"),
        "score_value": to_float(score),
        "score_display": display_score(score),
        "score_band": policy.band(score),
        "score_label": policy.band_label(score),
        "source_document": safe_attr(source, "source_document", "source_file", "kaynak_belge", default=None) or "—",
        "created_at_display": _date_text(safe_attr(source, "created_at", "created_on", "eklenme_tarihi", default=None)),
    }
    if include_person:
        payload.update({
            "personnel_name": safe_attr(source, "personnel_name", "full_name", "ad_soyad", default="Personel"),
            "registry_no": safe_attr(source, "registry_no", "sicil_no", default="—"),
            "general_comment": safe_attr(source, "general_comment", "description", "aciklama", "açıklama", default=""),
        })
    return payload


def build_person_archive_payload(
    rows: Iterable[Any],
    current_user: Any,
    target_user_id: Any,
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    policy = build_archive_policy(settings)
    detail_allowed = can_view_archive_detail(current_user, target_user_id)
    if not detail_allowed:
        raise PermissionError("Bu geçmiş karne detayına erişim yetkiniz bulunmamaktadır.")

    records = [normalize_archive_row(row, policy=policy, include_person=True) for row in rows]
    scores = [record["score_value"] for record in records if isinstance(record.get("score_value"), (int, float))]
    low_records = [record for record in records if record.get("score_band") == "low"]
    high_records = [record for record in records if record.get("score_band") == "high"]
    return {
        "ok": True,
        "module": "AI Karar Destek Merkezi",
        "scope": "Geçmiş Yıl Karne ve Puan Arşivi",
        "detail_allowed": True,
        "record_count": len(records),
        "low_record_count": len(low_records),
        "high_record_count": len(high_records),
        "average_score": round(sum(scores) / len(scores), 2) if scores else None,
        "average_score_display": display_score(round(sum(scores) / len(scores), 2)) if scores else "—",
        "trend_label": trend_label(scores),
        "risk_note": risk_level_from_history(scores, policy.low_score_limit),
        "records": records,
        "safety_note": "Bu çıktı idari karar değildir; geçmiş kayıtları insan denetimli değerlendirmeye yardımcı olur.",
        "marker": "BYS360_AI_DECISION_FAZ7_PERSON_ARCHIVE_PAYLOAD",
    }


def build_archive_summary_payload(
    rows: Iterable[Any],
    current_user: Any,
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not can_view_archive_summary(current_user):
        raise PermissionError("Bu arşiv özetine erişim yetkiniz bulunmamaktadır.")
    policy = build_archive_policy(settings)
    by_year: dict[int | str, dict[str, Any]] = defaultdict(lambda: {
        "record_count": 0,
        "score_total": 0.0,
        "score_count": 0,
        "low_count": 0,
        "high_count": 0,
    })
    by_band: dict[str, int] = defaultdict(int)
    for row in rows:
        record = normalize_archive_row(row, policy=policy, include_person=False)
        year = record.get("period_year") or "Yıl Bilgisi Yok"
        bucket = by_year[year]
        bucket["record_count"] += 1
        score = record.get("score_value")
        if isinstance(score, (int, float)):
            bucket["score_total"] += float(score)
            bucket["score_count"] += 1
        if record.get("score_band") == "low":
            bucket["low_count"] += 1
        if record.get("score_band") == "high":
            bucket["high_count"] += 1
        by_band[record.get("score_label") or "Diğer"] += 1

    year_rows = []
    for year, data in by_year.items():
        avg = round(data["score_total"] / data["score_count"], 2) if data["score_count"] else None
        year_rows.append({
            "period_year": year,
            "record_count": data["record_count"],
            "average_score": avg,
            "average_score_display": display_score(avg),
            "low_count": data["low_count"],
            "high_count": data["high_count"],
        })
    year_rows.sort(key=lambda item: str(item["period_year"]), reverse=True)
    return {
        "ok": True,
        "module": "AI Karar Destek Merkezi",
        "scope": "Geçmiş Karne Arşivi Özeti",
        "detail_allowed": False,
        "summary_only": True,
        "record_count": sum(item["record_count"] for item in year_rows),
        "years": year_rows,
        "score_distribution": dict(by_band),
        "safety_note": "Bu özet kişi detayı içermez; kapsam dışı personel verisi gösterilmez.",
        "marker": "BYS360_AI_DECISION_FAZ7_ARCHIVE_SUMMARY_PAYLOAD",
    }
