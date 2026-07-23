from __future__ import annotations

import logging

# BYS360_PHASE7_REPORT_CATEGORY_AVERAGE_SIGNATURE_FIX_V1
from collections.abc import Iterable
from typing import Any

"""Kategori ortalaması hesaplama servisi.

Bu servis rapor, karne ve personel görünürlüğünde kişi detayı sızdırmadan
kategori ortalaması üretir. Eski ve yeni çağrı şekillerini birlikte destekler:

- build_category_average_summary_for_users(items, selected_category=..., period=...)
- build_category_average_summary_for_users(employee_ids, period_id=..., category_label=...)

Özellikle /performance/reports rotasının kullandığı period_id/category_label
sözleşmesi korunur.
"""

logger = logging.getLogger(__name__)

PRIVACY_NOTE = "Kategori ortalaması kişi detayı göstermeden hesaplanır; kişi detayı gösterilmez."
FINAL_STATUS = "tamamlandi"


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def _safe_round(value: Any) -> float | None:
    number = _safe_float(value)
    if number is None:
        return None
    return round(number, 2)


def _score_value(item: Any) -> float | None:
    """Değerlendirme/özet nesnesinden güvenli puan okur."""
    for attr in (
        "report_final_score",
        "final_total_100",
        "final_score",
        "average_score",
        "avg_score",
        "score",
        "total_score",
    ):
        value = _safe_float(getattr(item, attr, None))
        if value is not None:
            return value
    if isinstance(item, dict):
        for key in (
            "report_final_score",
            "final_total_100",
            "final_score",
            "average_score",
            "avg_score",
            "score",
            "total_score",
        ):
            value = _safe_float(item.get(key))
            if value is not None:
                return value
    return None


def _normalize_label(label: Any) -> str:
    try:
        from app.services.personnel.categories import normalize_personnel_category_label

        return normalize_personnel_category_label(label)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        text = str(label or "").strip()
        return text or "Diğer"


def _employee_category_label(user: Any) -> str:
    try:
        from app.services.personnel.categories import get_user_personnel_category_label

        return _normalize_label(get_user_personnel_category_label(user))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/category_stats.py")
    for attr in ("personnel_category", "category_label", "performance_category_label"):
        value = getattr(user, attr, None)
        if value:
            return _normalize_label(value)
    category = getattr(user, "performance_category", None)
    for attr in ("label", "name", "title"):
        value = getattr(category, attr, None)
        if value:
            return _normalize_label(value)
    return "Diğer"


def _period_id_from_period(period: Any) -> int | None:
    value = getattr(period, "id", None)
    try:
        return int(value) if value is not None else None
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def _is_id_like(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        int(value)
        return True
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def _clean_ids(items: Iterable[Any] | None) -> list[int]:
    clean: list[int] = []
    for item in items or []:
        if _is_id_like(item):
            try:
                clean.append(int(item))
            except Exception:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/category_stats.py:122)")
                continue
    return clean


def _summary_payload(
    *,
    values: list[float],
    category_label: str | None = None,
    period_id: int | None = None,
) -> dict[str, Any]:
    avg = round(sum(values) / len(values), 2) if values else 0.0
    label = _normalize_label(category_label) if category_label else "Tüm Kategoriler"
    return {
        "enabled": True,
        "available": bool(values),
        "category_label": label,
        "selected_category": label,
        "period_id": int(period_id or 0),
        "average_score": avg,
        "category_average": avg,
        "average": avg,
        "count": len(values),
        "sample_count": len(values),
        "detail_visible": False,
        "person_detail_visible": False,
        "privacy_note": PRIVACY_NOTE,
    }


def _query_evaluations(
    *,
    employee_ids: list[int] | None = None,
    period_id: int | None = None,
    category_label: str | None = None,
) -> list[Any]:
    """Tamamlanmış değerlendirmeleri güvenli şekilde sorgular; hata olursa boş döner."""
    try:
        from sqlalchemy.orm import joinedload

        from app.models import PerformanceEvaluation, User
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return []

    try:
        query = PerformanceEvaluation.query.options(joinedload(PerformanceEvaluation.employee))
        if hasattr(PerformanceEvaluation, "status"):
            query = query.filter(PerformanceEvaluation.status == FINAL_STATUS)
        if period_id:
            query = query.filter(PerformanceEvaluation.period_id == int(period_id))
        if employee_ids:
            query = query.filter(PerformanceEvaluation.employee_id.in_([int(item) for item in employee_ids]))
        if category_label:
            label = _normalize_label(category_label)
            try:
                query = query.join(User, User.id == PerformanceEvaluation.employee_id)
                if hasattr(User, "personnel_category"):
                    query = query.filter(User.personnel_category == label)
            except Exception:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                # Join tarafında sorun olursa kullanıcı filtresi olmadan devam edilir;
                # sonuçlar aşağıdaki post-filter ile yine gizlilikli işlenir.
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/performance/category_stats.py:183)")
        rows = list(query.all())
        if category_label:
            label = _normalize_label(category_label)
            rows = [row for row in rows if _employee_category_label(getattr(row, "employee", None)) == label]
        return rows
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return []


def build_category_average_for_evaluation(
    evaluation: Any = None,
    user: Any = None,
    period: Any = None,
    *,
    period_id: int | None = None,
    category_label: str | None = None,
) -> dict[str, Any]:
    """Tek değerlendirme bağlamında kategori ortalaması üretir."""
    employee = user or getattr(evaluation, "employee", None)
    resolved_period_id = period_id or getattr(evaluation, "period_id", None) or _period_id_from_period(period or getattr(evaluation, "period", None))
    label = category_label or _employee_category_label(employee)
    rows = _query_evaluations(employee_ids=None, period_id=resolved_period_id, category_label=label)
    values = [score for row in rows if (score := _score_value(row)) is not None and score > 0]
    if not values:
        score = _score_value(evaluation) if evaluation is not None else None
        values = [score] if score is not None and score > 0 else []
    payload = _summary_payload(values=values, category_label=label, period_id=resolved_period_id)
    payload["period_title"] = getattr(period or getattr(evaluation, "period", None), "title", None) or "Dönem"
    return payload


def build_category_average_for_user(
    user: Any = None,
    period: Any = None,
    *,
    period_id: int | None = None,
    category_label: str | None = None,
) -> dict[str, Any]:
    """Kullanıcının kategorisi için kişi detaysız ortalama üretir."""
    resolved_period_id = period_id or _period_id_from_period(period)
    label = category_label or _employee_category_label(user)
    rows = _query_evaluations(employee_ids=None, period_id=resolved_period_id, category_label=label)
    values = [score for row in rows if (score := _score_value(row)) is not None and score > 0]
    return _summary_payload(values=values, category_label=label, period_id=resolved_period_id)


def build_category_average_summary_for_users(
    items: Iterable[Any] | None = None,
    selected_category: str | None = None,
    period: Any = None,
    *,
    period_id: int | None = None,
    category_label: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Rapor ekranı için kişi detayı döndürmeyen kategori ortalaması özeti.

    Yeni rapor rotası bu fonksiyonu `period_id=` ve `category_label=` ile çağırır.
    Eski çağrılar da `selected_category=` ve `period=` ile desteklenir.
    """
    resolved_period_id = period_id or _period_id_from_period(period)
    resolved_label = category_label or selected_category

    item_list = list(items or [])
    employee_ids = _clean_ids(item_list)

    if employee_ids or resolved_period_id or resolved_label:
        rows = _query_evaluations(employee_ids=employee_ids, period_id=resolved_period_id, category_label=resolved_label)
        values = [score for row in rows if (score := _score_value(row)) is not None and score > 0]
    else:
        values = [score for item in item_list if (score := _score_value(item)) is not None and score > 0]

    return _summary_payload(values=values, category_label=resolved_label, period_id=resolved_period_id)


__all__ = [
    "build_category_average_for_evaluation",
    "build_category_average_for_user",
    "build_category_average_summary_for_users",
]

# BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_PRIVACY_MARKER
# Kategori ortalaması kişi detayı göstermeden hesaplanmalıdır.
try:
    from app.services.performance.phase2_category_center import (
        PRIVACY_NOTE as PHASE2_CATEGORY_PRIVACY_NOTE,
    )
except Exception:
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    PHASE2_CATEGORY_PRIVACY_NOTE = "Kategori ortalaması kişi detayı göstermeden hesaplanır; kişi detayı gösterilmez."

