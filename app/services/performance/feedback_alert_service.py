from __future__ import annotations

from app.core.datetime_utils import utc_now
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from app.models import FeedbackMeeting, FeedbackRequest, Notification, User
from app.services.mail_service import send_email as send_plain_email
from app.services.message_service import notify_user

PENDING_REQUEST_STATUSES = {"bekliyor", "incelendi"}
ACTIVE_MEETING_STATUSES = {"planlandi", "ertelendi"}
REQUEST_REMINDER_DAYS = 2
REQUEST_SLA_DAYS = 5
MEETING_REMINDER_WINDOW_HOURS = 24
MEETING_OVERDUE_GRACE_HOURS = 2


def _full_name(user: Any) -> str:
    if not user:
        return "-"
    return (
        getattr(user, "full_name", None)
        or f"{getattr(user, 'ad', '')} {getattr(user, 'soyad', '')}".strip()
        or getattr(user, "email", None)
        or "-"
    )

def _request_manager_ids(feedback_request: FeedbackRequest | None) -> set[int]:
    ids: set[int] = set()
    if not feedback_request:
        return ids
    for field in (
        getattr(feedback_request, "level_1_manager_id", None),
        getattr(feedback_request, "level_2_manager_id", None),
        getattr(feedback_request, "level_3_manager_id", None),
        getattr(feedback_request, "scheduled_by_id", None),
    ):
        try:
            if field is not None:
                ids.add(int(field))
        except (TypeError, ValueError):
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/feedback_alert_service.py:45)")
            continue
    return ids

def _request_age_days(feedback_request: FeedbackRequest, now: datetime) -> int:
    requested_at = getattr(feedback_request, "requested_at", None) or now
    return max(int((now - requested_at).total_seconds() // 86400), 0)

def _request_is_open(feedback_request: FeedbackRequest) -> bool:
    return (getattr(feedback_request, "status", None) or "") in PENDING_REQUEST_STATUSES

def _meeting_start_dt(meeting: FeedbackMeeting) -> datetime | None:
    if not getattr(meeting, "meeting_date", None) or not getattr(meeting, "meeting_start", None):
        return None
    return datetime.combine(meeting.meeting_date, meeting.meeting_start)

def _meeting_end_dt(meeting: FeedbackMeeting) -> datetime | None:
    if not getattr(meeting, "meeting_date", None) or not getattr(meeting, "meeting_end", None):
        return None
    return datetime.combine(meeting.meeting_date, meeting.meeting_end)

def _meeting_is_active(meeting: FeedbackMeeting) -> bool:
    return (getattr(meeting, "status", None) or "") in ACTIVE_MEETING_STATUSES

def _meeting_within_window(meeting: FeedbackMeeting, now: datetime, hours: int) -> bool:
    if not _meeting_is_active(meeting):
        return False
    start_dt = _meeting_start_dt(meeting)
    if not start_dt:
        return False
    return now <= start_dt <= now + timedelta(hours=hours)

def _meeting_is_overdue(meeting: FeedbackMeeting, now: datetime) -> bool:
    if not _meeting_is_active(meeting):
        return False
    end_dt = _meeting_end_dt(meeting)
    if not end_dt:
        return False
    return end_dt < now - timedelta(hours=MEETING_OVERDUE_GRACE_HOURS)

def _notification_exists(*, user_id: int | None, notification_type: str, source_type: str, source_id: int | None) -> bool:
    if not user_id or not source_id:
        return False
    return Notification.query.filter_by(
        user_id=user_id,
        notification_type=notification_type,
        source_type=source_type,
        source_id=source_id,
        is_read=False,
    ).first() is not None

def _safe_email(user: User | None) -> str:
    raw = (getattr(user, "email", None) or "").strip()
    if "@" not in raw or " " in raw:
        return ""
    return raw

def _request_link(feedback_request: FeedbackRequest) -> str:
    return f"/performance/feedback-requests/{feedback_request.id}"

def _meeting_link(meeting: FeedbackMeeting) -> str:
    return f"/performance/feedback-meetings/{meeting.id}"

def build_feedback_alert_dashboard(requests_list: list[Any], meetings: list[Any], *, today=None, now: datetime | None = None) -> dict[str, Any]:
    now = now or utc_now()
    today = today or now.date()

    open_requests = [req for req in requests_list if _request_is_open(req)]
    request_alerts: list[dict[str, Any]] = []
    meeting_alerts: list[dict[str, Any]] = []
    manager_stats: dict[int, dict[str, Any]] = defaultdict(lambda: {
        "manager_id": None,
        "manager_name": "-",
        "open_requests": 0,
        "sla_risk_requests": 0,
        "upcoming_meetings": 0,
        "overdue_meetings": 0,
        "next_meeting_text": "-",
        "max_request_age_days": 0,
    })

    for req in open_requests:
        age_days = _request_age_days(req, now)
        manager_ids = _request_manager_ids(req)
        manager_names = [
            _full_name(getattr(req, "level_1_manager", None)),
            _full_name(getattr(req, "level_2_manager", None)),
            _full_name(getattr(req, "level_3_manager", None)),
        ]
        manager_names = [name for name in manager_names if name and name != "-"]
        if age_days >= REQUEST_REMINDER_DAYS:
            tone = "critical" if age_days >= REQUEST_SLA_DAYS else "watch"
            kind = "SLA riski" if age_days >= REQUEST_SLA_DAYS else "Hatırlatma"
            request_alerts.append({
                "request_id": req.id,
                "tone": tone,
                "kind": kind,
                "employee_name": _full_name(getattr(req, "employee", None)),
                "period_title": getattr(getattr(req, "period", None), "title", None) or "-",
                "status": getattr(req, "status", None) or "-",
                "age_days": age_days,
                "manager_text": ", ".join(manager_names) or "Yönetici çözümlenemedi",
                "detail": (getattr(req, "reason", None) or "Talep açıklaması girilmedi.").strip()[:220],
            })
        for manager_id in manager_ids:
            row = manager_stats[int(manager_id)]
            row["manager_id"] = int(manager_id)
            manager_user = next((item for item in [getattr(req, "level_1_manager", None), getattr(req, "level_2_manager", None), getattr(req, "level_3_manager", None)] if getattr(item, "id", None) == int(manager_id)), None)
            row["manager_name"] = _full_name(manager_user)
            row["open_requests"] += 1
            row["max_request_age_days"] = max(row["max_request_age_days"], age_days)
            if age_days >= REQUEST_SLA_DAYS:
                row["sla_risk_requests"] += 1

    for meeting in meetings:
        if _meeting_within_window(meeting, now, MEETING_REMINDER_WINDOW_HOURS):
            start_dt = _meeting_start_dt(meeting)
            meeting_alerts.append({
                "meeting_id": meeting.id,
                "tone": "watch",
                "kind": "Yaklaşan görüşme",
                "employee_name": _full_name(getattr(meeting, "employee", None)),
                "manager_name": _full_name(getattr(meeting, "manager", None)),
                "when_text": start_dt.strftime("%d.%m.%Y %H:%M") if start_dt else "-",
                "status": getattr(meeting, "status", None) or "-",
                "location": getattr(meeting, "location", None) or "Konum girilmedi",
            })
        if _meeting_is_overdue(meeting, now):
            end_dt = _meeting_end_dt(meeting)
            hours_late = round(max((now - end_dt).total_seconds() / 3600, 0), 1) if end_dt else 0
            meeting_alerts.append({
                "meeting_id": meeting.id,
                "tone": "critical",
                "kind": "Geciken görüşme",
                "employee_name": _full_name(getattr(meeting, "employee", None)),
                "manager_name": _full_name(getattr(meeting, "manager", None)),
                "when_text": end_dt.strftime("%d.%m.%Y %H:%M") if end_dt else "-",
                "status": getattr(meeting, "status", None) or "-",
                "location": getattr(meeting, "location", None) or "Konum girilmedi",
                "hours_late": hours_late,
            })

        manager_id = getattr(meeting, "manager_id", None)
        if manager_id:
            row = manager_stats[int(manager_id)]
            row["manager_id"] = int(manager_id)
            row["manager_name"] = _full_name(getattr(meeting, "manager", None))
            if _meeting_within_window(meeting, now, MEETING_REMINDER_WINDOW_HOURS):
                row["upcoming_meetings"] += 1
            if _meeting_is_overdue(meeting, now):
                row["overdue_meetings"] += 1
            start_dt = _meeting_start_dt(meeting)
            current_text = row.get("next_meeting_text") or "-"
            if start_dt and (current_text == "-" or start_dt.strftime("%d.%m.%Y %H:%M") < current_text):
                row["next_meeting_text"] = start_dt.strftime("%d.%m.%Y %H:%M")

    request_alerts.sort(key=lambda item: (-int(item["age_days"]), item["employee_name"]))
    meeting_alerts.sort(key=lambda item: (0 if item["tone"] == "critical" else 1, item["when_text"]))
    manager_rows = sorted(
        manager_stats.values(),
        key=lambda row: (-int(row["sla_risk_requests"]), -int(row["overdue_meetings"]), -int(row["open_requests"]), row["manager_name"]),
    )

    alert_counts = {
        "open_requests": len(open_requests),
        "request_reminder_candidates": sum(1 for item in request_alerts if item["kind"] == "Hatırlatma"),
        "request_sla_risks": sum(1 for item in request_alerts if item["kind"] == "SLA riski"),
        "meetings_next_24h": sum(1 for item in meeting_alerts if item["kind"] == "Yaklaşan görüşme"),
        "meeting_overdue": sum(1 for item in meeting_alerts if item["kind"] == "Geciken görüşme"),
        "manager_hotspots": sum(1 for row in manager_rows if row["open_requests"] or row["overdue_meetings"]),
    }

    runner_rules = {
        "request_reminder_days": REQUEST_REMINDER_DAYS,
        "request_sla_days": REQUEST_SLA_DAYS,
        "meeting_window_hours": MEETING_REMINDER_WINDOW_HOURS,
        "meeting_overdue_hours": MEETING_OVERDUE_GRACE_HOURS,
        "today_text": today.strftime("%d.%m.%Y") if hasattr(today, "strftime") else str(today),
    }

    return {
        "alert_counts": alert_counts,
        "request_alerts": request_alerts[:12],
        "meeting_alerts": meeting_alerts[:12],
        "manager_rows": manager_rows[:12],
        "runner_rules": runner_rules,
    }

def dispatch_feedback_alerts(
    requests_list: list[Any],
    meetings: list[Any],
    *,
    actor_user_id: int | None = None,
    now: datetime | None = None,
    send_mail: bool = False,
    limit: int = 250,
    request_audit_callback=None,
    meeting_audit_callback=None,
) -> dict[str, Any]:
    now = now or utc_now()
    counters = {
        "request_reminder_notifications": 0,
        "request_sla_notifications": 0,
        "meeting_reminder_notifications": 0,
        "meeting_overdue_notifications": 0,
        "email_success_count": 0,
        "email_failed_count": 0,
        "skipped_existing": 0,
        "touched_requests": 0,
        "touched_meetings": 0,
    }
    processed = 0

    for req in requests_list:
        if processed >= max(int(limit), 1):
            break
        if not _request_is_open(req):
            continue
        age_days = _request_age_days(req, now)
        if age_days < REQUEST_REMINDER_DAYS:
            continue

        is_sla = age_days >= REQUEST_SLA_DAYS
        notification_type = "performance_feedback_sla" if is_sla else "performance_feedback_followup"
        title = "Geri bildirim talebi SLA riski" if is_sla else "Geri bildirim talebi bekliyor"
        priority = "high" if is_sla else "warning"
        manager_users = [getattr(req, "level_1_manager", None), getattr(req, "level_2_manager", None), getattr(req, "level_3_manager", None)]
        sent_for_request = 0
        for manager in manager_users:
            user_id = getattr(manager, "id", None)
            if not user_id:
                continue
            if _notification_exists(user_id=user_id, notification_type=notification_type, source_type="feedback_request", source_id=req.id):
                counters["skipped_existing"] += 1
                continue
            notify_user(
                int(user_id),
                title=title,
                body=f"{_full_name(getattr(req, 'employee', None))} için açık geri bildirim talebi {age_days} gündür bekliyor. Talebi açıp yanıt veya randevu oluşturun.",
                notification_type=notification_type,
                source_type="feedback_request",
                source_id=req.id,
                link_url=_request_link(req),
                priority=priority,
            )
            sent_for_request += 1
            counters["request_sla_notifications" if is_sla else "request_reminder_notifications"] += 1
            if send_mail:
                email = _safe_email(manager)
                if email:
                    ok, _ = send_plain_email(
                        email,
                        f"BYS360 | {title}",
                        "\n".join([
                            f"Sayın {_full_name(manager)},",
                            "",
                            f"{_full_name(getattr(req, 'employee', None))} için geri bildirim talebi {age_days} gündür açık durumda.",
                            f"Dönem: {getattr(getattr(req, 'period', None), 'title', None) or '-'}",
                            f"Durum: {getattr(req, 'status', None) or '-'}",
                            "",
                            "Lütfen BYS360 üzerinden talebi inceleyiniz.",
                        ]),
                    )
                    counters["email_success_count" if ok else "email_failed_count"] += 1
        if sent_for_request:
            counters["touched_requests"] += 1
            processed += 1
            if callable(request_audit_callback):
                request_audit_callback(req, is_sla=is_sla, sent_count=sent_for_request, actor_user_id=actor_user_id, age_days=age_days)

    for meeting in meetings:
        if processed >= max(int(limit), 1):
            break
        is_upcoming = _meeting_within_window(meeting, now, MEETING_REMINDER_WINDOW_HOURS)
        is_overdue = _meeting_is_overdue(meeting, now)
        if not is_upcoming and not is_overdue:
            continue
        notification_type = "performance_feedback_meeting_overdue" if is_overdue else "performance_feedback_meeting_reminder"
        title = "Geri bildirim görüşmesi gecikti" if is_overdue else "Geri bildirim görüşmesi yaklaşıyor"
        priority = "high" if is_overdue else "normal"
        recipient_users = []
        if getattr(meeting, "employee", None):
            recipient_users.append(meeting.employee)
        if getattr(meeting, "manager", None):
            recipient_users.append(meeting.manager)
        feedback_request = getattr(meeting, "feedback_request", None)
        for manager in [getattr(feedback_request, "level_1_manager", None), getattr(feedback_request, "level_2_manager", None), getattr(feedback_request, "level_3_manager", None)]:
            if manager and getattr(manager, 'id', None) not in {getattr(item, 'id', None) for item in recipient_users}:
                recipient_users.append(manager)
        sent_for_meeting = 0
        when_text = (_meeting_start_dt(meeting) or now).strftime("%d.%m.%Y %H:%M")
        for user in recipient_users:
            user_id = getattr(user, "id", None)
            if not user_id:
                continue
            if _notification_exists(user_id=user_id, notification_type=notification_type, source_type="feedback_meeting", source_id=meeting.id):
                counters["skipped_existing"] += 1
                continue
            detail_text = (
                f"{_full_name(getattr(meeting, 'employee', None))} için görüşme {when_text} tarihinde planlı."
                if not is_overdue
                else f"{_full_name(getattr(meeting, 'employee', None))} için görüşme planlanan zamanını geçti. Kayıt durumunu güncelleyin."
            )
            notify_user(
                int(user_id),
                title=title,
                body=detail_text,
                notification_type=notification_type,
                source_type="feedback_meeting",
                source_id=meeting.id,
                link_url=_meeting_link(meeting),
                priority=priority,
            )
            sent_for_meeting += 1
            counters["meeting_overdue_notifications" if is_overdue else "meeting_reminder_notifications"] += 1
            if send_mail:
                email = _safe_email(user)
                if email:
                    ok, _ = send_plain_email(
                        email,
                        f"BYS360 | {title}",
                        "\n".join([
                            f"Sayın {_full_name(user)} ,".replace(" ,", ","),
                            "",
                            detail_text,
                            f"Konum/Bağlantı: {getattr(meeting, 'location', None) or '-'}",
                            f"Durum: {getattr(meeting, 'status', None) or '-'}",
                            "",
                            "BYS360 üzerinden randevu kaydını açabilirsiniz.",
                        ]),
                    )
                    counters["email_success_count" if ok else "email_failed_count"] += 1
        if sent_for_meeting:
            counters["touched_meetings"] += 1
            processed += 1
            if callable(meeting_audit_callback):
                meeting_audit_callback(meeting, is_overdue=is_overdue, sent_count=sent_for_meeting, actor_user_id=actor_user_id)

    return counters