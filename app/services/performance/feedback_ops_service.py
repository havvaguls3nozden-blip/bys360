from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta
from typing import Any

from app.core.datetime_utils import utc_now

STATUS_LABELS = {
    "bekliyor": "Bekliyor",
    "incelendi": "İncelendi",
    "cevaplandi": "Cevaplandı",
    "kapatildi": "Kapatıldı",
    "randevulandi": "Randevulandı",
    "gorusme_tamamlandi": "Görüşme tamamlandı",
    "randevu_ertelendi": "Randevu ertelendi",
    "randevu_iptal": "Randevu iptal",
    "planlandi": "Planlandı",
    "tamamlandi": "Tamamlandı",
    "ertelendi": "Ertelendi",
    "iptal_edildi": "İptal edildi",
}


PENDING_REQUEST_STATUSES = {"bekliyor", "incelendi"}
SCHEDULED_REQUEST_STATUSES = {"randevulandi", "gorusme_tamamlandi", "randevu_ertelendi", "randevu_iptal"}
ACTIVE_MEETING_STATUSES = {"planlandi", "ertelendi"}


def _full_name(user: Any) -> str:
    if not user:
        return "-"
    return (
        getattr(user, "full_name", None)
        or f"{getattr(user, 'ad', '')} {getattr(user, 'soyad', '')}".strip()
        or "-"
    )


def _status_label(value: str | None) -> str:
    raw = (value or "").strip()
    return STATUS_LABELS.get(raw, raw or "-")


def _meeting_window_label(meeting: Any) -> str:
    if not meeting:
        return "-"
    date_text = meeting.meeting_date.strftime("%d.%m.%Y") if getattr(meeting, "meeting_date", None) else "-"
    start_text = meeting.meeting_start.strftime("%H:%M") if getattr(meeting, "meeting_start", None) else "--:--"
    end_text = meeting.meeting_end.strftime("%H:%M") if getattr(meeting, "meeting_end", None) else "--:--"
    return f"{date_text} · {start_text} - {end_text}"


def _is_request_overdue(request_row: Any, today: date, *, threshold_days: int = 3) -> bool:
    if not request_row or (getattr(request_row, "status", "") or "").strip() not in PENDING_REQUEST_STATUSES:
        return False
    requested_at = getattr(request_row, "requested_at", None)
    if not requested_at:
        return False
    requested_date = requested_at.date() if isinstance(requested_at, datetime) else requested_at
    return requested_date <= (today - timedelta(days=threshold_days))


def build_feedback_operations_dashboard(requests_list: list[Any], meetings: list[Any], *, today: date | None = None) -> dict[str, Any]:
    today = today or utc_now().date()
    pending_requests = [row for row in requests_list if (getattr(row, "status", "") or "").strip() in PENDING_REQUEST_STATUSES]
    overdue_requests = [row for row in pending_requests if _is_request_overdue(row, today)]
    scheduled_requests = [row for row in requests_list if (getattr(row, "status", "") or "").strip() in SCHEDULED_REQUEST_STATUSES]

    upcoming_meetings = [
        meeting
        for meeting in meetings
        if getattr(meeting, "meeting_date", None)
        and meeting.meeting_date >= today
        and (getattr(meeting, "status", "") or "").strip() != "iptal_edildi"
    ]
    delayed_meetings = [
        meeting
        for meeting in meetings
        if (getattr(meeting, "status", "") or "").strip() == "ertelendi"
        or (
            getattr(meeting, "meeting_date", None)
            and meeting.meeting_date < today
            and (getattr(meeting, "status", "") or "").strip() == "planlandi"
        )
    ]

    manager_counter: Counter[tuple[int, str]] = Counter()
    for meeting in upcoming_meetings:
        manager = getattr(meeting, "manager", None)
        manager_id = getattr(manager, "id", None) or getattr(meeting, "manager_id", None)
        if not manager_id:
            continue
        manager_counter[(int(manager_id), _full_name(manager))] += 1

    busiest_managers = [
        {"manager_id": manager_id, "manager_name": manager_name, "meeting_count": count}
        for (manager_id, manager_name), count in manager_counter.most_common(8)
    ]

    action_items: list[dict[str, Any]] = []
    for req in overdue_requests[:8]:
        action_items.append(
            {
                "tone": "critical",
                "kind": "Talep",
                "title": f"{_full_name(getattr(req, 'employee', None))} · {_status_label(getattr(req, 'status', None))}",
                "meta": getattr(getattr(req, "period", None), "title", None) or "Dönem bilgisi yok",
                "detail": f"Talep {_meeting_window_label(getattr(req, 'meeting', None)) if getattr(req, 'meeting', None) else 'henüz randevuya bağlanmadı'}. Talep tarihi: {req.requested_at.strftime('%d.%m.%Y %H:%M') if getattr(req, 'requested_at', None) else '-'}",
                "request_id": getattr(req, "id", None),
            }
        )
    for meeting in delayed_meetings[:8]:
        action_items.append(
            {
                "tone": "watch",
                "kind": "Randevu",
                "title": f"{_full_name(getattr(meeting, 'employee', None))} · {_status_label(getattr(meeting, 'status', None))}",
                "meta": _full_name(getattr(meeting, "manager", None)),
                "detail": _meeting_window_label(meeting),
                "meeting_id": getattr(meeting, "id", None),
                "request_id": getattr(getattr(meeting, "feedback_request", None), "id", None),
            }
        )
    action_items = action_items[:10]

    return {
        "ops_counts": {
            "total_requests": len(requests_list),
            "pending_requests": len(pending_requests),
            "overdue_requests": len(overdue_requests),
            "scheduled_requests": len(scheduled_requests),
            "upcoming_meetings": len(upcoming_meetings),
            "delayed_meetings": len(delayed_meetings),
        },
        "pending_requests": pending_requests[:12],
        "overdue_requests": overdue_requests[:12],
        "upcoming_meetings": upcoming_meetings[:12],
        "delayed_meetings": delayed_meetings[:12],
        "busiest_managers": busiest_managers,
        "action_items": action_items,
        "status_labels": STATUS_LABELS,
    }


def _normalize_range(start_value: time | None, end_value: time | None) -> tuple[time | None, time | None]:
    if not start_value or not end_value:
        return start_value, end_value
    if start_value >= end_value:
        return start_value, end_value
    return start_value, end_value


def _time_range(start_value: time | None, end_value: time | None) -> str:
    start_text = start_value.strftime("%H:%M") if start_value else "--:--"
    end_text = end_value.strftime("%H:%M") if end_value else "--:--"
    return f"{start_text} - {end_text}"


def _ranges_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return start_a < end_b and end_a > start_b


def build_feedback_schedule_preview(
    request_row: Any,
    meetings: list[Any],
    *,
    meeting_date: date,
    selected_start: time | None = None,
    selected_end: time | None = None,
    business_start: time = time(9, 0),
    business_end: time = time(17, 30),
    slot_minutes: int = 30,
    default_duration_minutes: int = 60,
) -> dict[str, Any]:
    employee_id = getattr(request_row, "employee_id", None)
    manager_ids = {
        getattr(request_row, "level_1_manager_id", None),
        getattr(request_row, "level_2_manager_id", None),
        getattr(request_row, "level_3_manager_id", None),
    }
    manager_ids = {int(item) for item in manager_ids if item is not None}

    related = []
    for meeting in meetings:
        if getattr(meeting, "meeting_date", None) != meeting_date:
            continue
        if getattr(meeting, "feedback_request_id", None) == getattr(request_row, "id", None):
            continue
        if getattr(meeting, "employee_id", None) == employee_id or getattr(meeting, "manager_id", None) in manager_ids:
            related.append(meeting)

    related.sort(key=lambda item: (getattr(item, "meeting_start", None) or time.min, getattr(item, "meeting_end", None) or time.min, getattr(item, "id", 0)))

    items = []
    for meeting in related:
        owner_type = "personel" if getattr(meeting, "employee_id", None) == employee_id else "amir"
        items.append(
            {
                "meeting_id": getattr(meeting, "id", None),
                "owner_type": owner_type,
                "owner_name": _full_name(getattr(meeting, "employee", None) if owner_type == "personel" else getattr(meeting, "manager", None)),
                "time_range": _time_range(getattr(meeting, "meeting_start", None), getattr(meeting, "meeting_end", None)),
                "status": _status_label(getattr(meeting, "status", None)),
                "location": getattr(meeting, "location", None) or "Konum girilmedi",
                "meeting_type": getattr(meeting, "meeting_type", None) or "-",
            }
        )

    selected_conflict = None
    selected_start, selected_end = _normalize_range(selected_start, selected_end)
    if selected_start and selected_end and selected_start < selected_end:
        for meeting in related:
            existing_start = getattr(meeting, "meeting_start", None)
            existing_end = getattr(meeting, "meeting_end", None)
            if not existing_start or not existing_end:
                continue
            if _ranges_overlap(selected_start, selected_end, existing_start, existing_end):
                selected_conflict = {
                    "meeting_id": getattr(meeting, "id", None),
                    "owner_type": "personel" if getattr(meeting, "employee_id", None) == employee_id else "amir",
                    "owner_name": _full_name(getattr(meeting, "employee", None) if getattr(meeting, "employee_id", None) == employee_id else getattr(meeting, "manager", None)),
                    "time_range": _time_range(existing_start, existing_end),
                    "status": _status_label(getattr(meeting, "status", None)),
                }
                break

    suggestions: list[dict[str, str]] = []
    cursor = datetime.combine(meeting_date, business_start)
    business_limit = datetime.combine(meeting_date, business_end)
    duration = timedelta(minutes=max(default_duration_minutes, slot_minutes))
    step = timedelta(minutes=slot_minutes)
    while cursor + duration <= business_limit and len(suggestions) < 8:
        slot_start = cursor.time()
        slot_end = (cursor + duration).time()
        if not any(
            _ranges_overlap(slot_start, slot_end, m_start, m_end)
            for meeting in related
            if (m_start := getattr(meeting, "meeting_start", None)) and (m_end := getattr(meeting, "meeting_end", None))
        ):
            suggestions.append(
                {
                    "start": slot_start.strftime("%H:%M"),
                    "end": slot_end.strftime("%H:%M"),
                    "label": f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}",
                }
            )
        cursor += step

    return {
        "meeting_date": meeting_date.isoformat(),
        "meeting_count": len(items),
        "items": items,
        "selected_conflict": selected_conflict,
        "suggestions": suggestions,
        "has_conflict": selected_conflict is not None,
    }