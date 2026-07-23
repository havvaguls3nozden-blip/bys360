from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models import PerformanceEvaluation
from app.services.mail_service import send_published_evaluation_notifications
from app.services.performance.low_score_process_service import ensure_low_score_processes_for_period
from app.services.performance.period_state_guard import (
    validate_publish_window,
    validate_unpublish_allowed,
)
from app.services.publish_service import (
    publish_evaluation as core_publish_evaluation,
    publish_period_results as core_publish_period_results,
    summarize_skip_reasons,
    unpublish_evaluation as core_unpublish_evaluation,
    unpublish_period_results as core_unpublish_period_results,
)


def publish_period_results(period, actor: Any = None):
    if not period:
        return {
            "period_id": None,
            "published_count": 0,
            "skipped": [{"reason": "Dönem bulunamadı."}],
            "skip_reasons_summary": [("Dönem bulunamadı.", 1)],
            "published_evaluation_ids": [],
        }

    ok, message = validate_publish_window(period)
    if not ok:
        return {
            "period_id": getattr(period, "id", None),
            "published_count": 0,
            "skipped": [{"reason": message}],
            "skip_reasons_summary": [(message, 1)],
            "published_evaluation_ids": [],
        }

    # BYS360_PHASE6_1_LOW_SCORE_AUTO_ON_PUBLISH
    ensure_low_score_processes_for_period(period, actor_user_id=getattr(actor, "id", None))
    db.session.flush()
    result = core_publish_period_results(period=period, acted_by=actor)
    db.session.commit()
    notification_result = send_published_evaluation_notifications(
        period,
        result.get("published_evaluation_ids", []),
        actor_user_id=getattr(actor, "id", None),
    )
    db.session.commit()
    result["period_id"] = period.id
    result["notification_result"] = notification_result
    result["skip_reasons_summary"] = summarize_skip_reasons(result.get("skipped"))
    return result


def unpublish_period_results(period, actor: Any = None):
    if not period:
        return {
            "period_id": None,
            "unpublished_count": 0,
            "unpublished_evaluation_ids": [],
        }

    ok, message = validate_unpublish_allowed(period)
    if not ok:
        return {
            "period_id": getattr(period, "id", None),
            "unpublished_count": 0,
            "unpublished_evaluation_ids": [],
            "message": message,
        }

    result = core_unpublish_period_results(period=period, acted_by=actor)
    db.session.commit()
    result["period_id"] = period.id
    return result

def publish_single_evaluation(evaluation_id: int | None, period, actor: Any = None):
    """Seçili dönemde tek personel sonucunu personele açar.

    Toplu yayın akışını bozmadan, yalnızca seçilen değerlendirme kaydını yayınlar.
    70 altı Başkan onayı, yayın kilidi ve tamamlanma kontrolleri merkezi
    publish policy üzerinden korunur.
    """
    if not period:
        return {
            "ok": False,
            "period_id": None,
            "evaluation_id": evaluation_id,
            "published_count": 0,
            "message": "Dönem bulunamadı.",
            "notification_result": {},
        }

    if not evaluation_id:
        return {
            "ok": False,
            "period_id": period.id,
            "evaluation_id": None,
            "published_count": 0,
            "message": "Yayınlanacak personel kaydı seçilmedi.",
            "notification_result": {},
        }

    evaluation = db.session.get(PerformanceEvaluation, int(evaluation_id))
    if not evaluation or int(getattr(evaluation, "period_id", 0) or 0) != int(period.id):
        return {
            "ok": False,
            "period_id": period.id,
            "evaluation_id": evaluation_id,
            "published_count": 0,
            "message": "Seçilen değerlendirme bu döneme ait değil veya bulunamadı.",
            "notification_result": {},
        }

    ok, message = core_publish_evaluation(evaluation, acted_by=actor)
    # Başarısız yayında bile düşük performans süreç kaydı / yayın kilidi gibi
    # kontrol kayıtları oluşmuş olabilir; bu izler kaybolmasın.
    db.session.commit()

    notification_result = {}
    if ok:
        notification_result = send_published_evaluation_notifications(
            period,
            [evaluation.id],
            actor_user_id=getattr(actor, "id", None),
        )
        db.session.commit()

    return {
        "ok": bool(ok),
        "period_id": period.id,
        "evaluation_id": evaluation.id,
        "employee_id": getattr(evaluation, "employee_id", None),
        "published_count": 1 if ok else 0,
        "message": message,
        "notification_result": notification_result,
    }


def unpublish_single_evaluation(evaluation_id: int | None, period, actor: Any = None):
    """Seçili dönemde tek personel sonucunu personel görünümünden kaldırır."""
    if not period:
        return {
            "ok": False,
            "period_id": None,
            "evaluation_id": evaluation_id,
            "unpublished_count": 0,
            "message": "Dönem bulunamadı.",
        }

    if not evaluation_id:
        return {
            "ok": False,
            "period_id": period.id,
            "evaluation_id": None,
            "unpublished_count": 0,
            "message": "Yayından kaldırılacak personel kaydı seçilmedi.",
        }

    evaluation = db.session.get(PerformanceEvaluation, int(evaluation_id))
    if not evaluation or int(getattr(evaluation, "period_id", 0) or 0) != int(period.id):
        return {
            "ok": False,
            "period_id": period.id,
            "evaluation_id": evaluation_id,
            "unpublished_count": 0,
            "message": "Seçilen değerlendirme bu döneme ait değil veya bulunamadı.",
        }

    ok, message = core_unpublish_evaluation(evaluation, acted_by=actor)
    db.session.commit()
    return {
        "ok": bool(ok),
        "period_id": period.id,
        "evaluation_id": evaluation.id,
        "employee_id": getattr(evaluation, "employee_id", None),
        "unpublished_count": 1 if ok else 0,
        "message": message,
    }
