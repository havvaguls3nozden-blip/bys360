
"""BYS360 AI Karar Destek Faz 3 kategori görünürlüğü entegrasyonu.

Faz 2 kategori/grup özetleri bu katmandan geçtiğinde kullanıcı kapsamına göre
filtrelenir. Personel için kişi detayı yoktur; yönetici için yalnızca kendi
birim/kategori kapsamı görünür.

BYS360_AI_DECISION_FAZ3_CATEGORY_VISIBILITY_INTEGRATION
"""
from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models import PerformanceEvaluation, User
from app.services.ai_decision.visibility_scope import build_ai_decision_scope


def _score_bucket(score: float | None) -> str:
    try:
        value = float(score or 0)
    except (TypeError, ValueError):
        value = 0.0
    if value and value < 70:
        return "Düşük Performans Dikkat Alanı"
    if value >= 90:
        return "Yüksek Başarı Alanı"
    if value:
        return "Beklenen Aralık"
    return "Tamamlanmamış Kayıt"


def build_visible_category_group_summary(*, acting_user: Any, period_id: int | None = None) -> dict[str, Any]:
    scope = build_ai_decision_scope(acting_user)
    query = db.session.query(PerformanceEvaluation).join(User, PerformanceEvaluation.employee_id == User.id)
    if period_id:
        query = query.filter(PerformanceEvaluation.period_id == int(period_id))

    if not scope.can_view_global_summary:
        clauses = []
        user_id = getattr(acting_user, "id", None)
        if user_id and scope.can_view_own_summary:
            clauses.append(PerformanceEvaluation.employee_id == user_id)
        if user_id:
            clauses.append(PerformanceEvaluation.level_1_evaluator_id == user_id)
            clauses.append(PerformanceEvaluation.level_2_evaluator_id == user_id)
            clauses.append(PerformanceEvaluation.level_3_evaluator_id == user_id)
        if scope.can_view_unit_scope:
            if scope.allowed_unit_names:
                clauses.append(User.birim.in_(list(scope.allowed_unit_names)))
            if scope.allowed_upper_unit_names:
                clauses.append(User.ust_birim.in_(list(scope.allowed_upper_unit_names)))
        if scope.can_view_category_scope and scope.allowed_category_labels:
            clauses.append(User.personnel_category.in_(list(scope.allowed_category_labels)))
        if clauses:
            combined = clauses[0]
            for clause in clauses[1:]:
                combined = combined | clause
            query = query.filter(combined)
        else:
            query = query.filter(False)

    rows = query.limit(5000).all()
    grouped: dict[str, dict[str, Any]] = {}
    for evaluation in rows:
        employee = getattr(evaluation, "employee", None)
        category = (getattr(employee, "personnel_category", None) or "Diğer").strip() if employee else "Diğer"
        bucket = grouped.setdefault(
            category,
            {
                "category": category,
                "evaluation_count": 0,
                "published_count": 0,
                "low_score_count": 0,
                "high_score_count": 0,
                "score_sum": 0.0,
                "score_count": 0,
                "signals": {},
            },
        )
        bucket["evaluation_count"] += 1
        if getattr(evaluation, "is_published_to_employee", False):
            bucket["published_count"] += 1
        score = getattr(evaluation, "final_total_100", None)
        try:
            score_value = float(score or 0)
        except (TypeError, ValueError):
            score_value = 0.0
        if score_value:
            bucket["score_sum"] += score_value
            bucket["score_count"] += 1
        if score_value and score_value < 70:
            bucket["low_score_count"] += 1
        if score_value >= 90:
            bucket["high_score_count"] += 1
        signal = _score_bucket(score_value)
        bucket["signals"][signal] = bucket["signals"].get(signal, 0) + 1

    summaries: list[dict[str, Any]] = []
    for item in grouped.values():
        avg = round(item["score_sum"] / item["score_count"], 2) if item["score_count"] else None
        summaries.append(
            {
                "category": item["category"],
                "evaluation_count": item["evaluation_count"],
                "published_count": item["published_count"],
                "low_score_count": item["low_score_count"],
                "high_score_count": item["high_score_count"],
                "average_score": avg,
                "signals": item["signals"],
                "privacy_note": "Bu özet kişi detayı içermez.",
            }
        )

    summaries.sort(key=lambda item: (item["category"] or ""))
    return {
        "ok": True,
        "data": {
            "period_id": period_id,
            "scope": scope.to_dict(),
            "category_groups": summaries,
            "category_count": len(summaries),
            "privacy_notice": "Kategori görünürlüğü kullanıcının rol, birim ve kategori kapsamına göre sınırlandırılmıştır.",
        },
    }
