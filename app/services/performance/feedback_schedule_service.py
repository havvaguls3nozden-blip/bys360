from __future__ import annotations



from datetime import datetime
from typing import Any, Mapping

from app.extensions import db
from app.models import FeedbackMeeting
from app.services.mail_service import send_feedback_meeting_created_mail
from app.services.performance.feedback_audit_service import record_feedback_audit_event
from app.performance.feedback_helpers import (
    _feedback_manager_ids,
    _find_feedback_meeting_conflict,
    _notify_feedback_meeting_created,
    _serialize_feedback_meeting_state,
    _serialize_feedback_request_state,
)
import logging
logger = logging.getLogger(__name__)


def schedule_feedback_meeting(*, feedback_request: Any, actor_user: Any, form_data: Mapping[str, Any]) -> dict[str, Any]:
    meeting_date_raw = str(form_data.get("meeting_date") or "").strip()
    meeting_start_raw = str(form_data.get("meeting_start") or "").strip()
    meeting_end_raw = str(form_data.get("meeting_end") or "").strip()
    meeting_type = str(form_data.get("meeting_type") or "yuz_yuze").strip()
    location = str(form_data.get("location") or "").strip()
    note = str(form_data.get("note") or "").strip()

    if not meeting_date_raw or not meeting_start_raw or not meeting_end_raw:
        return {"ok": False, "category": "warning", "message": "Tarih ve saat alanları zorunludur."}

    try:
        meeting_date = datetime.strptime(meeting_date_raw, "%Y-%m-%d").date()
        meeting_start = datetime.strptime(meeting_start_raw, "%H:%M").time()
        meeting_end = datetime.strptime(meeting_end_raw, "%H:%M").time()
    except ValueError:
        return {"ok": False, "category": "warning", "message": "Tarih veya saat formatı geçersiz."}

    if meeting_start >= meeting_end:
        return {"ok": False, "category": "warning", "message": "Başlangıç saati bitiş saatinden küçük olmalıdır."}

    related_manager_ids = _feedback_manager_ids(feedback_request) or {getattr(actor_user, "id", None)}
    conflict_meeting, conflict_message = _find_feedback_meeting_conflict(
        manager_ids=related_manager_ids,
        employee_id=getattr(feedback_request, "employee_id", None),
        meeting_date=meeting_date,
        meeting_start=meeting_start,
        meeting_end=meeting_end,
    )
    if conflict_meeting:
        return {"ok": False, "category": "danger", "message": conflict_message}

    try:
        meeting = FeedbackMeeting(
            feedback_request_id=feedback_request.id,
            employee_id=feedback_request.employee_id,
            manager_id=actor_user.id,
            meeting_date=meeting_date,
            meeting_start=meeting_start,
            meeting_end=meeting_end,
            location=location or None,
            meeting_type=meeting_type,
            note=note or None,
            status="planlandi",
        )
        db.session.add(meeting)
        db.session.flush()

        previous_request_state = _serialize_feedback_request_state(feedback_request)
        feedback_request.status = "randevulandi"
        feedback_request.scheduled_by_id = actor_user.id
        feedback_request.scheduled_meeting_id = meeting.id

        _notify_feedback_meeting_created(meeting)
        actor_name = f"{getattr(actor_user, 'ad', '')} {getattr(actor_user, 'soyad', '')}".strip() or getattr(actor_user, 'full_name', None) or "Yönetici"
        record_feedback_audit_event(
            entity_type="feedback_meeting",
            entity_id=meeting.id,
            action="feedback_meeting_created",
            actor_user_id=actor_user.id,
            summary=f"{actor_name} görüşme randevusu planladı.",
            new_data=_serialize_feedback_meeting_state(meeting),
        )
        record_feedback_audit_event(
            entity_type="feedback_request",
            entity_id=feedback_request.id,
            action="feedback_request_status_updated",
            actor_user_id=actor_user.id,
            summary="Talep randevuya bağlandı.",
            old_data=previous_request_state,
            new_data=_serialize_feedback_request_state(feedback_request),
        )
        db.session.commit()
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/feedback_schedule_service.py | line=94")
        db.session.rollback()
        return {"ok": False, "category": "danger", "message": f"Randevu oluşturulurken hata oluştu: {exc}"}

    mail_result = send_feedback_meeting_created_mail(meeting)
    failed_count = int((mail_result or {}).get("failed_count", 0) or 0)
    if failed_count > 0:
        return {
            "ok": True,
            "meeting": meeting,
            "mail_failed": True,
            "message": "Randevu oluşturuldu. Uygulama içi bildirimler kaydedildi, ancak bazı e-posta bildirimleri gönderilemedi.",
        }
    return {
        "ok": True,
        "meeting": meeting,
        "mail_failed": False,
        "message": "Randevu oluşturuldu ve bildirimler gönderildi.",
    }


__all__ = ["schedule_feedback_meeting"]
