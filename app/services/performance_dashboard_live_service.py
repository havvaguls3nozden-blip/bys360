from __future__ import annotations

import logging

"""BYS360 Performans Dashboard canlı veri servisi.

Bu servis /performance/dashboard ekranının temsilî sayılarla değil, mevcut
PostgreSQL/SQLAlchemy verisiyle çalışması için hazırlanmıştır. Tüm sorgular
korumalıdır; tablo/kolon uyumsuzluğu veya boş veri durumunda dashboard beyaz
ekrana düşmez, güvenli boş veri üretir.
"""

from collections import defaultdict
from datetime import timedelta
from typing import Any

from sqlalchemy import func, or_

from app.core.datetime_utils import utc_now
from app.models import (
    EvaluationAssignment,
    MailLog,
    Notification,
    PerformanceEvaluation,
    PerformanceLowScoreProcess,
    PerformancePeriod,
    User,
)
from app.route_support import safe_count, safe_db_rollback
from app.services.ui_context.scope import build_user_scope_context

logger = logging.getLogger(__name__)

BYS360_PERFORMANCE_DASHBOARD_LIVE_SERVICE_OK = True

STATUS_LABELS = {
    "published": "Yayınlandı",
    "president": "Başkan Onayı",
    "pending": "Bekleyen",
    "returned": "İade",
}

CATEGORY_ORDER = ["Güvenlik", "Temizlik", "İdari Personel", "Teknik Personel", "Deneme Süreli Personel", "Diğer"]
CATEGORY_SHORT_LABEL = {
    "Güvenlik": "Güvenlik",
    "Temizlik": "Temizlik",
    "İdari Personel": "İdari",
    "Teknik Personel": "Teknik",
    "Deneme Süreli Personel": "Deneme",
    "Diğer": "Diğer",
}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _pct(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    try:
        return round((float(numerator) / float(denominator)) * 100, 1)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 0.0


def _rollback_empty(value: Any) -> Any:
    safe_db_rollback()
    return value


def _active_period() -> PerformancePeriod | None:
    try:
        return (
            PerformancePeriod.query
            .filter_by(is_active=True)
            .order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
            .first()
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return _rollback_empty(None)


def _period_label(period: PerformancePeriod | None) -> str:
    if not period:
        return "Aktif dönem yok"
    return str(getattr(period, "title", None) or getattr(period, "name", None) or f"Dönem #{getattr(period, 'id', '')}")


def _period_range(period: PerformancePeriod | None) -> str:
    if not period:
        return "Dönem seçildiğinde veriler otomatik güncellenir."
    start = getattr(period, "start_date", None)
    end = getattr(period, "end_date", None)
    if start and end:
        try:
            return f"{start.strftime('%d.%m.%Y')} – {end.strftime('%d.%m.%Y')}"
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return f"{start} – {end}"
    return "Tarih aralığı tanımlı değil"


def _scope_ids(user, base_context: dict[str, Any] | None = None) -> list[int]:
    base_context = base_context or {}
    scope = base_context.get("dashboard_scope") or {}
    ids = list(scope.get("scope_user_ids") or [])
    if ids:
        return [int(x) for x in ids if x]
    try:
        scope = build_user_scope_context(user, None)
        ids = list(scope.get("scope_user_ids") or [])
        if ids:
            return [int(x) for x in ids if x]
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        safe_db_rollback()
    current_id = getattr(user, "id", None)
    return [int(current_id)] if current_id else []


def _evaluation_query(period_id: int | None, scope_user_ids: list[int]):
    q = PerformanceEvaluation.query
    if period_id:
        q = q.filter(PerformanceEvaluation.period_id == period_id)
    if scope_user_ids:
        q = q.filter(PerformanceEvaluation.employee_id.in_(scope_user_ids))
    else:
        q = q.filter(False)
    return q


def _assignment_query(period_id: int | None, scope_user_ids: list[int]):
    q = EvaluationAssignment.query
    if period_id:
        q = q.filter(EvaluationAssignment.period_id == period_id)
    if scope_user_ids:
        q = q.filter(EvaluationAssignment.employee_id.in_(scope_user_ids))
    else:
        q = q.filter(False)
    return q


def _total_evaluations(period_id: int | None, scope_user_ids: list[int], base_context: dict[str, Any]) -> int:
    base_total = _safe_int(base_context.get("total_evaluations"))
    if base_total:
        return base_total
    try:
        return safe_count(_evaluation_query(period_id, scope_user_ids), label="live_dashboard_total_evaluations")
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return _rollback_empty(0)


def _completed_evaluations(period_id: int | None, scope_user_ids: list[int], base_context: dict[str, Any]) -> int:
    base_completed = _safe_int(base_context.get("completed_evaluations"))
    if base_completed:
        return base_completed
    try:
        return safe_count(
            _evaluation_query(period_id, scope_user_ids).filter(
                or_(
                    PerformanceEvaluation.status.in_(("tamamlandi", "yayinda", "published", "final")),
                    PerformanceEvaluation.final_total_100 > 0,
                    PerformanceEvaluation.is_published_to_employee.is_(True),
                )
            ),
            label="live_dashboard_completed_evaluations",
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return _rollback_empty(0)


def _low_score_count(period_id: int | None, scope_user_ids: list[int]) -> int:
    try:
        return safe_count(
            _evaluation_query(period_id, scope_user_ids).filter(
                PerformanceEvaluation.final_total_100 > 0,
                PerformanceEvaluation.final_total_100 < 70,
            ),
            label="live_dashboard_low_score_count",
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return _rollback_empty(0)


def _published_count(period_id: int | None, scope_user_ids: list[int]) -> int:
    try:
        return safe_count(
            _evaluation_query(period_id, scope_user_ids).filter(
                PerformanceEvaluation.is_published_to_employee.is_(True)
            ),
            label="live_dashboard_published_count",
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return _rollback_empty(0)


def _president_pending_count(period_id: int | None, scope_user_ids: list[int]) -> int:
    try:
        q = PerformanceLowScoreProcess.query
        if period_id:
            q = q.filter(PerformanceLowScoreProcess.period_id == period_id)
        if scope_user_ids:
            q = q.filter(PerformanceLowScoreProcess.employee_id.in_(scope_user_ids))
        else:
            q = q.filter(False)
        q = q.filter(
            PerformanceLowScoreProcess.president_approved_at.is_(None),
            PerformanceLowScoreProcess.president_rejected_at.is_(None),
        )
        count = safe_count(q, label="live_dashboard_president_pending_count")
        if count:
            return count
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        safe_db_rollback()
    return _low_score_count(period_id, scope_user_ids)


def _returned_count(period_id: int | None, scope_user_ids: list[int]) -> int:
    try:
        q = PerformanceLowScoreProcess.query
        if period_id:
            q = q.filter(PerformanceLowScoreProcess.period_id == period_id)
        if scope_user_ids:
            q = q.filter(PerformanceLowScoreProcess.employee_id.in_(scope_user_ids))
        else:
            q = q.filter(False)
        q = q.filter(PerformanceLowScoreProcess.president_rejected_at.isnot(None))
        return safe_count(q, label="live_dashboard_returned_count")
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return _rollback_empty(0)


def _approval_status(total: int, published: int, president_pending: int, returned: int) -> dict[str, Any]:
    pending = max(int(total or 0) - int(published or 0) - int(president_pending or 0) - int(returned or 0), 0)
    rows = [
        {"key": "published", "label": STATUS_LABELS["published"], "count": published, "percent": _pct(published, total), "tone": "green"},
        {"key": "president", "label": STATUS_LABELS["president"], "count": president_pending, "percent": _pct(president_pending, total), "tone": "blue"},
        {"key": "pending", "label": STATUS_LABELS["pending"], "count": pending, "percent": _pct(pending, total), "tone": "amber"},
        {"key": "returned", "label": STATUS_LABELS["returned"], "count": returned, "percent": _pct(returned, total), "tone": "red"},
    ]
    start = 0.0
    segments = []
    colors = {"green": "#2f9d57", "blue": "#2563eb", "amber": "#f59e0b", "red": "#dc2626"}
    for row in rows:
        end = start + (float(row["percent"]) * 3.6)
        if row["count"]:
            segments.append(f"{colors[row['tone']]} {start:.1f}deg {end:.1f}deg")
        start = end
    gradient = "conic-gradient(" + ", ".join(segments or ["#e5e7eb 0deg 360deg"]) + ")"
    return {"total": total, "rows": rows, "gradient": gradient}


def _completion_trend(period: PerformancePeriod | None, scope_user_ids: list[int], total: int) -> list[dict[str, Any]]:
    if not period or not getattr(period, "start_date", None) or not getattr(period, "end_date", None):
        value = _pct(0, total)
        return [{"label": "Başlangıç", "value": value, "x": 6, "y": 92}]
    try:
        start = period.start_date
        end = period.end_date
        days = max((end - start).days, 1)
        bucket_count = 8 if days <= 60 else 12
        bucket_days = max(days // bucket_count, 1)
        completed_dates = [
            row[0].date() if hasattr(row[0], "date") else row[0]
            for row in _assignment_query(getattr(period, "id", None), scope_user_ids)
            .filter(EvaluationAssignment.completed_at.isnot(None))
            .with_entities(EvaluationAssignment.completed_at)
            .all()
            if row and row[0]
        ]
        points = []
        for idx in range(bucket_count + 1):
            bucket_date = min(start + timedelta(days=bucket_days * idx), end)
            count = sum(1 for dt in completed_dates if dt and dt <= bucket_date)
            value = _pct(count, total)
            x = 6 + (88 / bucket_count) * idx
            y = 92 - (min(value, 100) * 0.82)
            label = bucket_date.strftime("%d.%m")
            points.append({"label": label, "value": round(value, 1), "x": round(x, 2), "y": round(y, 2)})
        if points and points[-1]["value"] == 0 and total:
            # Görev tamamlanma tarihi tutulmamışsa, en azından gerçek tamamlanan toplamını son noktada göster.
            completed_count = safe_count(
                _evaluation_query(getattr(period, "id", None), scope_user_ids).filter(PerformanceEvaluation.final_total_100 > 0),
                label="live_dashboard_trend_completed_fallback",
            )
            points[-1]["value"] = _pct(completed_count, total)
            points[-1]["y"] = round(92 - (min(points[-1]["value"], 100) * 0.82), 2)
        return points
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        safe_db_rollback()
        return [{"label": "Veri yok", "value": 0, "x": 6, "y": 92}]


def _category_averages(period_id: int | None, scope_user_ids: list[int]) -> list[dict[str, Any]]:
    base = {cat: {"score_sum": 0.0, "count": 0} for cat in CATEGORY_ORDER}
    try:
        rows = (
            _evaluation_query(period_id, scope_user_ids)
            .join(User, User.id == PerformanceEvaluation.employee_id)
            .filter(PerformanceEvaluation.final_total_100 > 0)
            .with_entities(User.personnel_category, func.avg(PerformanceEvaluation.final_total_100), func.count(PerformanceEvaluation.id))
            .group_by(User.personnel_category)
            .all()
        )
        for category, avg_score, count in rows:
            category = category or "Diğer"
            if category not in base:
                base["Diğer"]["score_sum"] += _safe_float(avg_score) * _safe_int(count)
                base["Diğer"]["count"] += _safe_int(count)
            else:
                base[category] = {"score_sum": _safe_float(avg_score) * _safe_int(count), "count": _safe_int(count)}
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        safe_db_rollback()
    output = []
    for category in CATEGORY_ORDER:
        count = base[category]["count"]
        avg = round(base[category]["score_sum"] / count, 1) if count else 0.0
        output.append({
            "label": CATEGORY_SHORT_LABEL.get(category, category),
            "full_label": category,
            "score": avg,
            "count": count,
            "height": max(6, min(100, avg)),
            "empty": count == 0,
        })
    return output


def _overdue_managers(period_id: int | None, scope_user_ids: list[int]) -> list[dict[str, Any]]:
    now = utc_now()
    rows_out: list[dict[str, Any]] = []
    try:
        rows = (
            _assignment_query(period_id, scope_user_ids)
            .join(User, User.id == EvaluationAssignment.evaluator_id)
            .filter(
                EvaluationAssignment.due_date.isnot(None),
                EvaluationAssignment.due_date < now,
                EvaluationAssignment.status.in_(("bekliyor", "kismen_tamamlandi")),
            )
            .with_entities(
                User.ad,
                User.soyad,
                func.count(EvaluationAssignment.id).label("task_count"),
                func.min(EvaluationAssignment.due_date).label("oldest_due"),
            )
            .group_by(User.id, User.ad, User.soyad)
            .order_by(func.min(EvaluationAssignment.due_date).asc())
            .limit(5)
            .all()
        )
        max_days = 1
        temp = []
        for ad, soyad, task_count, oldest_due in rows:
            days = max((now - oldest_due).days if oldest_due else 0, 0)
            max_days = max(max_days, days)
            temp.append({
                "name": f"{ad or ''} {soyad or ''}".strip() or "Tanımsız amir",
                "days": days,
                "task_count": _safe_int(task_count),
            })
        rows_out = [{**row, "percent": round((row["days"] / max_days) * 100, 1) if max_days else 0} for row in temp]
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        safe_db_rollback()
    return rows_out


def _risk_matrix(period_id: int | None, scope_user_ids: list[int]) -> dict[str, Any]:
    columns = ["90+", "80-89", "70-79", "60-69", "<60"]
    rows = {
        "Yüksek Risk": {col: 0 for col in columns},
        "İzlenmeli": {col: 0 for col in columns},
        "Dengeli": {col: 0 for col in columns},
    }
    try:
        scores = [
            _safe_float(row[0])
            for row in _evaluation_query(period_id, scope_user_ids)
            .filter(PerformanceEvaluation.final_total_100 > 0)
            .with_entities(PerformanceEvaluation.final_total_100)
            .all()
        ]
        for score in scores:
            if score >= 90:
                col = "90+"
            elif score >= 80:
                col = "80-89"
            elif score >= 70:
                col = "70-79"
            elif score >= 60:
                col = "60-69"
            else:
                col = "<60"
            if score < 70:
                row = "Yüksek Risk"
            elif score < 80:
                row = "İzlenmeli"
            else:
                row = "Dengeli"
            rows[row][col] += 1
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        safe_db_rollback()
    matrix_rows = []
    total = 0
    for label, values in rows.items():
        row_total = sum(values.values())
        total += row_total
        matrix_rows.append({"label": label, "values": [values[col] for col in columns], "total": row_total})
    totals = [sum(row["values"][idx] for row in matrix_rows) for idx in range(len(columns))]
    return {"columns": columns, "rows": matrix_rows, "totals": totals, "total": total}


def _low_score_density(period_id: int | None, scope_user_ids: list[int]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "low": 0})
    try:
        rows = (
            _evaluation_query(period_id, scope_user_ids)
            .join(User, User.id == PerformanceEvaluation.employee_id)
            .filter(PerformanceEvaluation.final_total_100 > 0)
            .with_entities(User.ust_birim, User.birim, PerformanceEvaluation.final_total_100)
            .all()
        )
        for ust_birim, birim, score in rows:
            unit = ust_birim or birim or "Birim bilgisi yok"
            grouped[unit]["total"] += 1
            if _safe_float(score) < 70:
                grouped[unit]["low"] += 1
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        safe_db_rollback()
    out = []
    for unit, item in grouped.items():
        total = item["total"]
        low = item["low"]
        out.append({"unit": unit, "total": total, "low": low, "percent": _pct(low, total)})
    return sorted(out, key=lambda x: (x["percent"], x["low"]), reverse=True)[:6]


def _recent_activity(user_id: int | None, period_id: int | None, scope_user_ids: list[int]) -> list[dict[str, Any]]:
    activities: list[dict[str, Any]] = []
    try:
        q = Notification.query
        if user_id:
            q = q.filter(Notification.user_id == user_id)
        for row in q.order_by(Notification.created_at.desc()).limit(4).all():
            activities.append({
                "tone": "blue" if not getattr(row, "is_read", False) else "green",
                "title": getattr(row, "title", None) or "Bildirim",
                "body": getattr(row, "body", None) or "Süreç bildirimi oluşturuldu.",
                "time": _format_time(getattr(row, "created_at", None)),
            })
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        safe_db_rollback()
    if len(activities) < 4:
        try:
            q = MailLog.query
            if period_id:
                q = q.filter(MailLog.related_period_id == period_id)
            for row in q.order_by(MailLog.sent_at.desc()).limit(4 - len(activities)).all():
                activities.append({
                    "tone": "green" if getattr(row, "is_success", False) else "red",
                    "title": getattr(row, "subject", None) or "E-posta kaydı",
                    "body": f"{getattr(row, 'recipient_email', '')} adresine bilgilendirme kaydı oluştu.",
                    "time": _format_time(getattr(row, "sent_at", None)),
                })
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            safe_db_rollback()
    if len(activities) < 4:
        try:
            q = PerformanceLowScoreProcess.query
            if period_id:
                q = q.filter(PerformanceLowScoreProcess.period_id == period_id)
            if scope_user_ids:
                q = q.filter(PerformanceLowScoreProcess.employee_id.in_(scope_user_ids))
            for row in q.order_by(PerformanceLowScoreProcess.created_at.desc()).limit(4 - len(activities)).all():
                activities.append({
                    "tone": "red",
                    "title": "Düşük performans süreci",
                    "body": "70 altı kayıt üst onay ve süreç takibi için işaretlendi.",
                    "time": _format_time(getattr(row, "created_at", None)),
                })
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            safe_db_rollback()
    return activities[:4]


def _format_time(value: Any) -> str:
    if not value:
        return "-"
    try:
        today = utc_now().date()
        date_value = value.date() if hasattr(value, "date") else value
        if date_value == today:
            return f"Bugün {value.strftime('%H:%M')}"
        if date_value == today - timedelta(days=1):
            return f"Dün {value.strftime('%H:%M')}"
        return value.strftime("%d.%m.%Y")
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return str(value)


def _trend_polyline(points: list[dict[str, Any]]) -> str:
    return " ".join(f"{row['x']},{row['y']}" for row in points)


def _decision_note(total: int, completion_rate: float, low_count: int, overdue_count: int, pending_president: int) -> str:
    if low_count > 0:
        return f"{low_count} düşük performans kaydı var; Başkan/üst onay ve gelişim takibi birlikte izlenmeli."
    if overdue_count > 0:
        return f"{overdue_count} geciken amir kaydı dönem kapanışını etkileyebilir; hatırlatma akışı kontrol edilmeli."
    if pending_president > 0:
        return f"{pending_president} kayıt üst onay bekliyor; yayın öncesi süreç zinciri tamamlanmalı."
    if total and completion_rate >= 90:
        return "Dönem kapanışı güçlü görünüyor; yayın öncesi görünürlük ve arşiv kontrolü yapılabilir."
    return "Dönem, görev, onay ve gelişim alanları canlı veriye göre izleniyor."


def build_live_performance_dashboard_context(user, base_context: dict[str, Any] | None = None) -> dict[str, Any]:
    base_context = base_context or {}
    period = base_context.get("active_period") or _active_period()
    period_id = getattr(period, "id", None)
    scope_user_ids = _scope_ids(user, base_context)

    total = _total_evaluations(period_id, scope_user_ids, base_context)
    completed = _completed_evaluations(period_id, scope_user_ids, base_context)
    completion_rate = _pct(completed, total)
    low_count = _low_score_count(period_id, scope_user_ids)
    published = _published_count(period_id, scope_user_ids)
    president_pending = _president_pending_count(period_id, scope_user_ids)
    returned = _returned_count(period_id, scope_user_ids)
    overdue_managers = _overdue_managers(period_id, scope_user_ids)
    overdue_count = len(overdue_managers)
    trend = _completion_trend(period, scope_user_ids, total)
    approval = _approval_status(total, published, president_pending, returned)

    category_rows = _category_averages(period_id, scope_user_ids)
    density_rows = _low_score_density(period_id, scope_user_ids)
    matrix = _risk_matrix(period_id, scope_user_ids)
    activities = _recent_activity(getattr(user, "id", None), period_id, scope_user_ids)

    return {
        "period_label": _period_label(period),
        "period_range": _period_range(period),
        "scope_count": len(scope_user_ids),
        "total_evaluations": total,
        "completed_evaluations": completed,
        "completion_rate": completion_rate,
        "published_count": published,
        "president_pending_count": president_pending,
        "low_score_count": low_count,
        "overdue_manager_count": overdue_count,
        "returned_count": returned,
        "trend": trend,
        "trend_polyline": _trend_polyline(trend),
        "category_averages": category_rows,
        "approval_status": approval,
        "overdue_managers": overdue_managers,
        "risk_matrix": matrix,
        "low_score_density": density_rows,
        "recent_activity": activities,
        "decision_note": _decision_note(total, completion_rate, low_count, overdue_count, president_pending),
        "has_real_data": bool(total or completed or low_count or published or president_pending or overdue_count or any(row.get("count") for row in category_rows)),
    }
