from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean
from typing import Any

from flask import current_app, has_request_context, request
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import AuditLog, FeedbackMeeting

logger = logging.getLogger(__name__)

PENDING_REQUEST_STATUSES = {"bekliyor", "incelendi"}

ACTION_LABELS = {
    "feedback_request_created": "Talep oluşturuldu",
    "feedback_request_status_updated": "Talep durumu güncellendi",
    "feedback_request_responded": "Personele yanıt verildi",
    "feedback_request_closed": "Talep kapatıldı",
    "feedback_request_alert_sent": "Talep hatırlatması gönderildi",
    "feedback_request_sla_alert_sent": "Talep SLA uyarısı gönderildi",
    "feedback_meeting_created": "Randevu planlandı",
    "feedback_meeting_status_updated": "Randevu güncellendi",
    "feedback_meeting_alert_sent": "Görüşme hatırlatması gönderildi",
    "feedback_meeting_overdue_alert_sent": "Görüşme gecikme uyarısı gönderildi",
    "feedback_digest_sent": "Yönetici özeti çalıştırıldı",
}

ACTION_TONES = {
    "feedback_request_created": "info",
    "feedback_request_status_updated": "watch",
    "feedback_request_responded": "positive",
    "feedback_request_closed": "neutral",
    "feedback_request_alert_sent": "watch",
    "feedback_request_sla_alert_sent": "critical",
    "feedback_meeting_created": "info",
    "feedback_meeting_status_updated": "watch",
    "feedback_meeting_alert_sent": "watch",
    "feedback_meeting_overdue_alert_sent": "critical",
    "feedback_digest_sent": "info",
}


def _safe_json(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/feedback_audit_service.py | line=56")
        return None

def _safe_load_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        payload = json.loads(value)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/feedback_audit_service.py | line=67")
        return {}

def _table_ready() -> bool:
    try:
        inspector = db.inspect(db.engine)
        return bool(inspector.has_table("audit_logs"))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/feedback_audit_service.py | line=76")
        return False

def _user_name(user: Any) -> str:
    if not user:
        return "Sistem"
    return (
        getattr(user, "full_name", None)
        or f"{getattr(user, 'ad', '')} {getattr(user, 'soyad', '')}".strip()
        or getattr(user, "email", None)
        or "Sistem"
    )

def _status_label(value: str | None) -> str:
    labels = {
        "bekliyor": "Bekliyor",
        "incelendi": "İncelendi",
        "cevaplandi": "Cevaplandı",
        "kapatildi": "Kapatıldı",
        "randevulandi": "Randevulandı",
        "gorusme_tamamlandi": "Görüşme tamamlandı",
        "randevu_ertelendi": "Randevu ertelendi",
        "randevu_iptal": "Randevu iptal edildi",
        "planlandi": "Planlandı",
        "tamamlandi": "Tamamlandı",
        "ertelendi": "Ertelendi",
        "iptal_edildi": "İptal edildi",
    }
    raw = (value or "").strip()
    return labels.get(raw, "Bilinmiyor") if raw else "-"

def _hours_between(start_value: datetime | None, end_value: datetime | None) -> float | None:
    if not start_value or not end_value:
        return None
    delta = end_value - start_value
    return round(delta.total_seconds() / 3600, 2)

def _audit_meta() -> tuple[str | None, str | None]:
    if not has_request_context():
        return None, None
    endpoint = request.endpoint
    ip_address = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "").strip()
        or request.remote_addr
    )
    return endpoint, ip_address

def record_feedback_audit_event(
    *,
    entity_type: str,
    entity_id: int | None,
    action: str,
    actor_user_id: int | None,
    summary: str,
    old_data: dict[str, Any] | None = None,
    new_data: dict[str, Any] | None = None,
) -> bool:
    if not entity_id or not action or not summary:
        return False
    if not _table_ready():
        current_app.logger.info(
            "Feedback audit atlandı; audit_logs tablosu hazır değil | entity=%s:%s action=%s",
            entity_type,
            entity_id,
            action,
        )
        return False
    endpoint, ip_address = _audit_meta()
    try:
        entry = AuditLog(
            user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data_json=_safe_json(old_data),
            new_data_json=_safe_json(new_data),
            summary=summary[:255],
            endpoint=endpoint,
            ip_address=ip_address,
        )
        db.session.add(entry)
        return True
    except SQLAlchemyError as exc:
        current_app.logger.warning(
            "Feedback audit kaydı yazılamadı | entity=%s:%s action=%s error=%s",
            entity_type,
            entity_id,
            action,
            exc,
        )
        return False

def _load_logs(*, request_ids: list[int], meeting_ids: list[int]) -> list[AuditLog]:
    if not _table_ready() or (not request_ids and not meeting_ids):
        return []
    clauses = []
    if request_ids:
        clauses.append((AuditLog.entity_type == "feedback_request") & (AuditLog.entity_id.in_(request_ids)))
    if meeting_ids:
        clauses.append((AuditLog.entity_type == "feedback_meeting") & (AuditLog.entity_id.in_(meeting_ids)))
    if not clauses:
        return []
    return (
        AuditLog.query.options(joinedload(AuditLog.user))  # type: ignore[arg-type]
        .filter(or_(*clauses))
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .all()
    )

def _timeline_rows(logs: list[AuditLog]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for log in logs:
        new_payload = _safe_load_json(getattr(log, "new_data_json", None))
        rows.append(
            {
                "id": log.id,
                "created_at": getattr(log, "created_at", None),
                "actor_name": _user_name(getattr(log, "user", None)),
                "action": log.action,
                "action_label": ACTION_LABELS.get(log.action, log.action),
                "summary": getattr(log, "summary", None) or ACTION_LABELS.get(log.action, log.action),
                "entity_type": log.entity_type,
                "entity_label": "Talep" if log.entity_type == "feedback_request" else "Randevu",
                "tone": ACTION_TONES.get(log.action, "neutral"),
                "status_label": _status_label(new_payload.get("status")),
            }
        )
    return rows

def get_feedback_request_timeline(request_id: int, *, limit: int = 20) -> list[dict[str, Any]]:
    if not request_id:
        return []
    meeting = FeedbackMeeting.query.filter_by(feedback_request_id=request_id).first()
    logs = _load_logs(request_ids=[request_id], meeting_ids=[meeting.id] if meeting else [])
    return _timeline_rows(logs[:limit])

def get_feedback_meeting_timeline(meeting_id: int, *, limit: int = 20) -> list[dict[str, Any]]:
    if not meeting_id:
        return []
    meeting = db.session.get(FeedbackMeeting, meeting_id)
    request_ids = [meeting.feedback_request_id] if meeting and getattr(meeting, "feedback_request_id", None) else []
    logs = _load_logs(request_ids=request_ids, meeting_ids=[meeting_id])
    return _timeline_rows(logs[:limit])

def build_feedback_audit_dashboard(requests_list: list[Any], meetings: list[Any], *, today=None) -> dict[str, Any]:
    now = utc_now()
    today = today or now.date()
    request_ids = [int(item.id) for item in requests_list if getattr(item, "id", None)]
    meeting_ids = [int(item.id) for item in meetings if getattr(item, "id", None)]
    logs = _load_logs(request_ids=request_ids, meeting_ids=meeting_ids)

    logs_by_request: dict[int, list[AuditLog]] = defaultdict(list)
    logs_by_meeting: dict[int, list[AuditLog]] = defaultdict(list)
    for log in logs:
        if log.entity_type == "feedback_request":
            logs_by_request[int(log.entity_id)].append(log)
        elif log.entity_type == "feedback_meeting":
            logs_by_meeting[int(log.entity_id)].append(log)

    meetings_by_request = {getattr(meeting, "feedback_request_id", None): meeting for meeting in meetings if getattr(meeting, "feedback_request_id", None)}

    response_hours_all: list[float] = []
    schedule_hours_all: list[float] = []
    completion_hours_all: list[float] = []
    manager_stats: dict[int, dict[str, Any]] = {}
    slow_requests: list[dict[str, Any]] = []

    def _ensure_manager(manager_id: int | None, manager_name: str) -> dict[str, Any] | None:
        if not manager_id:
            return None
        if manager_id not in manager_stats:
            manager_stats[manager_id] = {
                "manager_id": manager_id,
                "manager_name": manager_name,
                "assigned_requests": 0,
                "open_linked_requests": 0,
                "overdue_linked_requests": 0,
                "first_response_hours": [],
                "schedule_hours": [],
                "completion_hours": [],
                "response_count": 0,
                "scheduled_count": 0,
                "completed_count": 0,
            }
        return manager_stats[manager_id]

    for req in requests_list:
        request_created_at = getattr(req, "requested_at", None)
        [
            getattr(req, "level_1_manager_id", None),
            getattr(req, "level_2_manager_id", None),
            getattr(req, "level_3_manager_id", None),
        ]
        linked_managers = [
            (getattr(req, "level_1_manager", None), getattr(req, "level_1_manager_id", None)),
            (getattr(req, "level_2_manager", None), getattr(req, "level_2_manager_id", None)),
            (getattr(req, "level_3_manager", None), getattr(req, "level_3_manager_id", None)),
        ]
        pending = (getattr(req, "status", "") or "").strip() in PENDING_REQUEST_STATUSES
        overdue = bool(request_created_at and pending and request_created_at.date() <= (today - timedelta(days=3)))
        for manager_obj, manager_id in linked_managers:
            row = _ensure_manager(manager_id, _user_name(manager_obj))
            if not row:
                continue
            row["assigned_requests"] += 1
            if pending:
                row["open_linked_requests"] += 1
            if overdue:
                row["overdue_linked_requests"] += 1

        req_logs = sorted(logs_by_request.get(int(req.id), []), key=lambda item: (item.created_at or now, item.id))
        first_touch_log = next(
            (
                log for log in req_logs
                if log.action in {"feedback_request_status_updated", "feedback_request_responded", "feedback_request_closed"}
            ),
            None,
        )
        response_hours = _hours_between(request_created_at, getattr(first_touch_log, "created_at", None))
        if response_hours is not None:
            response_hours_all.append(response_hours)
            actor = getattr(first_touch_log, "user", None)
            row = _ensure_manager(getattr(first_touch_log, "user_id", None), _user_name(actor))
            if row:
                row["first_response_hours"].append(response_hours)
                row["response_count"] += 1

        meeting = meetings_by_request.get(getattr(req, "id", None))
        schedule_owner_id = getattr(req, "scheduled_by_id", None) or getattr(meeting, "manager_id", None)
        schedule_owner_name = _user_name(getattr(meeting, "manager", None)) if meeting else "-"
        schedule_hours = _hours_between(request_created_at, getattr(meeting, "created_at", None)) if meeting else None
        if schedule_hours is not None:
            schedule_hours_all.append(schedule_hours)
            row = _ensure_manager(schedule_owner_id, schedule_owner_name)
            if row:
                row["schedule_hours"].append(schedule_hours)
                row["scheduled_count"] += 1

        completion_log = None
        if meeting:
            meeting_logs = sorted(logs_by_meeting.get(int(meeting.id), []), key=lambda item: (item.created_at or now, item.id))
            completion_log = next(
                (
                    log for log in meeting_logs
                    if _safe_load_json(getattr(log, "new_data_json", None)).get("status") == "tamamlandi"
                ),
                None,
            )
        completion_hours = _hours_between(request_created_at, getattr(completion_log, "created_at", None))
        if completion_hours is not None:
            completion_hours_all.append(completion_hours)
            row = _ensure_manager(getattr(completion_log, "user_id", None), _user_name(getattr(completion_log, "user", None)))
            if row:
                row["completion_hours"].append(completion_hours)
                row["completed_count"] += 1

        if response_hours is not None and response_hours > 24:
            slow_requests.append(
                {
                    "request_id": req.id,
                    "employee_name": _user_name(getattr(req, "employee", None)),
                    "period_title": getattr(getattr(req, "period", None), "title", None) or "Dönem bilgisi yok",
                    "status_label": _status_label(getattr(req, "status", None)),
                    "hours": response_hours,
                    "kind": "İlk yanıt",
                }
            )
        if schedule_hours is not None and schedule_hours > 48:
            slow_requests.append(
                {
                    "request_id": req.id,
                    "employee_name": _user_name(getattr(req, "employee", None)),
                    "period_title": getattr(getattr(req, "period", None), "title", None) or "Dönem bilgisi yok",
                    "status_label": _status_label(getattr(req, "status", None)),
                    "hours": schedule_hours,
                    "kind": "Randevuya bağlama",
                }
            )

    manager_rows = []
    for row in manager_stats.values():
        avg_response = round(mean(row["first_response_hours"]), 2) if row["first_response_hours"] else None
        avg_schedule = round(mean(row["schedule_hours"]), 2) if row["schedule_hours"] else None
        avg_completion = round(mean(row["completion_hours"]), 2) if row["completion_hours"] else None
        manager_rows.append(
            {
                **row,
                "avg_response_hours": avg_response,
                "avg_schedule_hours": avg_schedule,
                "avg_completion_hours": avg_completion,
            }
        )
    manager_rows.sort(
        key=lambda item: (
            -(item.get("overdue_linked_requests") or 0),
            -(item.get("open_linked_requests") or 0),
            item.get("avg_response_hours") if item.get("avg_response_hours") is not None else 999999,
            item.get("manager_name") or "",
        )
    )

    recent_events = _timeline_rows(logs[:18])
    slow_requests.sort(key=lambda item: (-float(item.get("hours") or 0), item.get("employee_name") or ""))

    return {
        "audit_counts": {
            "event_count": len(logs),
            "request_count": len(requests_list),
            "meeting_count": len(meetings),
            "avg_first_response_hours": round(mean(response_hours_all), 2) if response_hours_all else None,
            "avg_schedule_hours": round(mean(schedule_hours_all), 2) if schedule_hours_all else None,
            "avg_completion_hours": round(mean(completion_hours_all), 2) if completion_hours_all else None,
            "open_requests": sum(1 for item in requests_list if (getattr(item, "status", "") or "").strip() in PENDING_REQUEST_STATUSES),
        },
        "manager_rows": manager_rows[:12],
        "recent_events": recent_events,
        "slow_requests": slow_requests[:12],
        "audit_ready": _table_ready(),
    }
