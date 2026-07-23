from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import (
    PersonnelSelfServiceRequest,
    PersonnelSelfServiceRequestEscalation,
    PersonnelSelfServiceRequestSlaPolicy,
    PersonnelSelfServiceRequestTask,
    User,
)
from app.route_registry import main_bp
from app.route_support import (
    consume_form_token,
    issue_form_token,
    manager_required,
    menu_key_required,
    safe_db_rollback,
    safe_render,
)

from .hr_personnel_operations_routes import (
    _current_scope_bundle,
    _full_name,
    _normalize_text,
    _request_in_scope,
    _request_priority_label,
    _request_status_label,
    _request_type_label,
    _safe_int,
    _sla_payload,
    _table_exists,
    _write_request_log,
)
from .hr_request_task_routes import _manager_pool

logger = logging.getLogger(__name__)


PRIORITY_ORDER = {"critical": 0, "high": 1, "normal": 2, "low": 3}
STATUS_CLOSED = {"approved", "rejected"}


def _policy_rows() -> list[PersonnelSelfServiceRequestSlaPolicy]:
    if not _table_exists("personnel_self_service_request_sla_policies"):
        return []
    return (
        PersonnelSelfServiceRequestSlaPolicy.query
        .order_by(PersonnelSelfServiceRequestSlaPolicy.sort_order.asc(), PersonnelSelfServiceRequestSlaPolicy.id.asc())
        .all()
    )


def _find_policy(request_type: str | None, priority: str | None) -> PersonnelSelfServiceRequestSlaPolicy | None:
    rows = [row for row in _policy_rows() if getattr(row, "is_active", True)]
    req = (request_type or "").strip().lower()
    pr = (priority or "").strip().lower()
    exact = next((row for row in rows if (row.request_type or "").strip().lower() == req and ((row.priority or "").strip().lower() == pr)), None)
    if exact:
        return exact
    generic = next((row for row in rows if (row.request_type or "").strip().lower() == req and not (row.priority or "").strip()), None)
    return generic


def _effective_due_at(row: PersonnelSelfServiceRequest) -> datetime | None:
    if getattr(row, "due_at", None):
        return row.due_at
    policy = _find_policy(getattr(row, "request_type", None), getattr(row, "priority", None))
    target_days = getattr(row, "sla_target_days", None) or getattr(policy, "target_days", None)
    anchor = getattr(row, "submitted_at", None) or getattr(row, "created_at", None)
    if anchor and target_days:
        return anchor + timedelta(days=int(target_days))
    return None


def _policy_payload(row: PersonnelSelfServiceRequest) -> dict[str, object] | None:
    policy = _find_policy(getattr(row, "request_type", None), getattr(row, "priority", None))
    if not policy and not getattr(row, "sla_target_days", None) and not getattr(row, "due_at", None):
        return None
    due_at = _effective_due_at(row)
    now = utc_now()
    days_remaining = None
    tone = "soft"
    label = "Takipsiz"
    if due_at:
        days_remaining = (due_at - now).days
        if (getattr(row, "status", None) or "draft") in STATUS_CLOSED:
            tone = "good"
            label = "Kapandı"
        elif days_remaining < 0:
            tone = "bad"
            label = f"{abs(days_remaining)} gün gecikmiş"
        elif days_remaining <= 1:
            tone = "warn"
            label = "Bugün / yarın doluyor"
        else:
            tone = "good"
            label = f"{days_remaining} gün kaldı"
    return {
        "policy": policy,
        "due_at": due_at,
        "days_remaining": days_remaining,
        "tone": tone,
        "label": label,
    }


def _escalation_rows(scope_user_ids: set[int]) -> list[PersonnelSelfServiceRequestEscalation]:
    if not _table_exists("personnel_self_service_request_escalations"):
        return []
    return (
        PersonnelSelfServiceRequestEscalation.query
        .join(PersonnelSelfServiceRequestEscalation.request)
        .filter(PersonnelSelfServiceRequest.user_id.in_(list(scope_user_ids)))
        .order_by(PersonnelSelfServiceRequestEscalation.escalated_at.desc().nullslast(), PersonnelSelfServiceRequestEscalation.id.desc())
        .all()
    )


def _request_rows(scope_user_ids: set[int]) -> list[PersonnelSelfServiceRequest]:
    if not _table_exists("personnel_self_service_requests"):
        return []
    return (
        PersonnelSelfServiceRequest.query
        .filter(PersonnelSelfServiceRequest.user_id.in_(list(scope_user_ids)))
        .order_by(PersonnelSelfServiceRequest.created_at.desc(), PersonnelSelfServiceRequest.id.desc())
        .all()
    )


def _avg_close_hours(rows: list[PersonnelSelfServiceRequest]) -> float:
    values = []
    for row in rows:
        if getattr(row, "closed_at", None) and (getattr(row, "submitted_at", None) or getattr(row, "created_at", None)):
            anchor = getattr(row, "submitted_at", None) or getattr(row, "created_at", None)
            values.append((row.closed_at - anchor).total_seconds() / 3600)
    return round(sum(values) / len(values), 1) if values else 0.0


def _analytics_payload(hr_scope: dict[str, object], scope_users: list[User], scope_user_ids: set[int]) -> dict[str, object]:
    rows = _request_rows(scope_user_ids)
    escalations = _escalation_rows(scope_user_ids)
    status_counts = Counter()
    type_counts = Counter()
    assignee_counts = Counter()
    aging = {"0_2": 0, "3_7": 0, "8_plus": 0}
    urgent_rows = []

    for row in rows:
        status = (getattr(row, "status", None) or "draft").strip().lower()
        status_counts[status] += 1
        type_counts[(getattr(row, "request_type", None) or "diger").strip().lower()] += 1
        open_task = None
        if hasattr(row, "tasks"):
            open_task = row.tasks.filter(PersonnelSelfServiceRequestTask.status.in_(["open", "in_progress"])).order_by(PersonnelSelfServiceRequestTask.id.desc()).first()
        if open_task and getattr(open_task, "assigned_to", None):
            assignee_counts[_full_name(open_task.assigned_to)] += 1
        if status not in STATUS_CLOSED:
            anchor = getattr(row, "submitted_at", None) or getattr(row, "created_at", None)
            age_days = (utc_now() - anchor).days if anchor else 0
            if age_days <= 2:
                aging["0_2"] += 1
            elif age_days <= 7:
                aging["3_7"] += 1
            else:
                aging["8_plus"] += 1
        sla = _policy_payload(row) or _sla_payload(row)
        escalation_count = row.escalations.count() if hasattr(row, "escalations") else 0
        is_urgent = False
        if sla and (sla.get("days_remaining") is not None) and sla.get("days_remaining") < 0 and status not in STATUS_CLOSED or escalation_count > 0 and status not in STATUS_CLOSED:
            is_urgent = True
        if is_urgent:
            urgent_rows.append({
                "id": int(row.id),
                "title": row.title,
                "user_name": _full_name(getattr(row, "user", None)),
                "request_type_label": _request_type_label(getattr(row, "request_type", None)),
                "priority_label": _request_priority_label(getattr(row, "priority", None)),
                "status_label": _request_status_label(status),
                "sla": sla,
                "handler_name": _full_name(getattr(row, "current_handler", None)),
                "escalation_count": escalation_count,
                "open_task": open_task,
            })

    urgent_rows.sort(key=lambda item: (((item.get("sla") or {}).get("days_remaining", 999999)), item.get("escalation_count", 0) * -1, item.get("title") or ""))

    top_assignees = [
        {"name": name, "count": count}
        for name, count in assignee_counts.most_common(6)
    ]
    type_rows = [
        {"label": _request_type_label(key), "count": count}
        for key, count in sorted(type_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    status_rows = [
        {"label": _request_status_label(key), "count": count}
        for key, count in sorted(status_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    recent_escalations = []
    for row in escalations[:8]:
        recent_escalations.append({
            "id": int(row.id),
            "request_id": int(row.request_id),
            "request_title": getattr(getattr(row, "request", None), "title", None) or "Talep",
            "from_name": _full_name(getattr(row, "escalated_from_user", None)),
            "to_name": _full_name(getattr(row, "escalated_to_user", None)),
            "by_name": _full_name(getattr(row, "escalated_by", None)),
            "level": int(getattr(row, "level", 1) or 1),
            "status": getattr(row, "status", None) or "open",
            "reason": getattr(row, "reason", None) or "-",
            "note": getattr(row, "note", None) or "",
            "at": getattr(row, "escalated_at", None) or getattr(row, "created_at", None),
        })
    return {
        "hr_scope": hr_scope,
        "selected_scope_mode": (hr_scope or {}).get("scope_mode") or "personal",
        "scope_label": (hr_scope or {}).get("scope_label") or "Kapsam",
        "analytics_summary": {
            "total": len(rows),
            "open": sum(1 for row in rows if (getattr(row, "status", None) or "draft") not in STATUS_CLOSED),
            "overdue": sum(1 for row in rows if ((_policy_payload(row) or _sla_payload(row) or {}).get("days_remaining", 999999) < 0 and (getattr(row, "status", None) or "draft") not in STATUS_CLOSED)),
            "escalated": sum(1 for row in rows if hasattr(row, "escalations") and row.escalations.count() > 0),
            "avg_close_hours": _avg_close_hours(rows),
            "policy_count": len([item for item in _policy_rows() if getattr(item, "is_active", True)]),
        },
        "aging": aging,
        "type_rows": type_rows,
        "status_rows": status_rows,
        "top_assignees": top_assignees,
        "urgent_rows": urgent_rows[:12],
        "recent_escalations": recent_escalations,
        "manager_rows": _manager_pool(scope_users),
        "escalation_token": issue_form_token("hr_personnel_request_escalate", scope="hr_request_analytics"),
    }


def _policy_payload_page(hr_scope: dict[str, object], scope_users: list[User], scope_user_ids: set[int]) -> dict[str, object]:
    rows = []
    for row in _policy_rows():
        rows.append({
            "id": int(row.id),
            "code": row.code,
            "request_type_label": _request_type_label(getattr(row, "request_type", None)),
            "priority_label": _request_priority_label(getattr(row, "priority", None) or "normal"),
            "request_type": getattr(row, "request_type", None),
            "priority": getattr(row, "priority", None),
            "title": row.title,
            "target_days": row.target_days,
            "first_response_hours": row.first_response_hours,
            "escalation_hours": row.escalation_hours,
            "owner_role": row.owner_role or "-",
            "note": row.note or "",
            "is_active": bool(getattr(row, "is_active", True)),
        })
    escalation_rows = []
    for row in _escalation_rows(scope_user_ids)[:10]:
        escalation_rows.append({
            "request_title": getattr(getattr(row, "request", None), "title", None) or "Talep",
            "to_name": _full_name(getattr(row, "escalated_to_user", None)),
            "from_name": _full_name(getattr(row, "escalated_from_user", None)),
            "status": getattr(row, "status", None) or "open",
            "level": int(getattr(row, "level", 1) or 1),
            "reason": getattr(row, "reason", None) or "-",
            "at": getattr(row, "escalated_at", None) or getattr(row, "created_at", None),
        })
    return {
        "hr_scope": hr_scope,
        "selected_scope_mode": (hr_scope or {}).get("scope_mode") or "personal",
        "scope_label": (hr_scope or {}).get("scope_label") or "Kapsam",
        "policy_rows": rows,
        "policy_token": issue_form_token("hr_request_sla_policy_save", scope="hr_request_sla_policy"),
        "recent_escalation_rows": escalation_rows,
        "manager_rows": _manager_pool(scope_users),
    }


@main_bp.route("/hr-management/personnel-operations/request-analytics")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_request_analytics():
    hr_scope, scope_users, scope_user_ids = _current_scope_bundle()
    payload = _analytics_payload(hr_scope, scope_users, scope_user_ids)
    return safe_render("hr_personnel_request_analytics.html", **payload)


@main_bp.route("/hr-management/personnel-operations/request-sla-policies")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_request_sla_policies():
    hr_scope, scope_users, scope_user_ids = _current_scope_bundle()
    payload = _policy_payload_page(hr_scope, scope_users, scope_user_ids)
    return safe_render("hr_personnel_request_sla_policies.html", **payload)


@main_bp.route("/hr-management/personnel-operations/request-sla-policies/save", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_request_sla_policy_save():
    hr_scope, scope_users, scope_user_ids = _current_scope_bundle()
    if not consume_form_token("hr_request_sla_policy_save", request.form.get("form_token"), scope="hr_request_sla_policy"):
        flash("SLA politika kaydı güvenlik doğrulaması başarısız oldu.", "danger")
        return redirect(url_for("main.hr_personnel_request_sla_policies", scope=(hr_scope or {}).get("scope_mode")))
    try:
        policy_id = _safe_int(request.form.get("policy_id"))
        code = _normalize_text(request.form.get("code"), 50)
        request_type = _normalize_text(request.form.get("request_type"), 50).lower()
        title = _normalize_text(request.form.get("title"), 255)
        priority = _normalize_text(request.form.get("priority"), 20).lower() or None
        target_days = max(1, _safe_int(request.form.get("target_days")) or 1)
        first_response_hours = _safe_int(request.form.get("first_response_hours"))
        escalation_hours = _safe_int(request.form.get("escalation_hours"))
        owner_role = _normalize_text(request.form.get("owner_role"), 50).lower() or None
        note = _normalize_text(request.form.get("note"), 2000) or None
        if not code or not request_type or not title:
            raise ValueError("Kod, talep tipi ve politika başlığı zorunludur.")
        row = PersonnelSelfServiceRequestSlaPolicy.query.get(policy_id) if policy_id else None
        if row is None:
            row = PersonnelSelfServiceRequestSlaPolicy(code=code)
        row.code = code
        row.request_type = request_type
        row.priority = priority
        row.title = title
        row.target_days = target_days
        row.first_response_hours = first_response_hours
        row.escalation_hours = escalation_hours
        row.owner_role = owner_role
        row.note = note
        row.is_active = str(request.form.get("is_active") or "").strip().lower() in {"1", "true", "on", "yes", "evet"}
        row.sort_order = _safe_int(request.form.get("sort_order")) or 0
        db.session.add(row)
        db.session.commit()
        flash("SLA politikası kaydedildi.", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(str(exc), "danger")
    return redirect(url_for("main.hr_personnel_request_sla_policies", scope=(hr_scope or {}).get("scope_mode")))


@main_bp.route("/hr-management/personnel-operations/request/<int:request_id>/escalate", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_request_escalate(request_id: int):
    hr_scope, scope_users, scope_user_ids = _current_scope_bundle()
    if not consume_form_token("hr_personnel_request_escalate", request.form.get("form_token"), scope="hr_request_analytics"):
        flash("Eskalasyon güvenlik doğrulaması başarısız oldu.", "danger")
        return redirect(url_for("main.hr_personnel_request_analytics", scope=(hr_scope or {}).get("scope_mode")))
    try:
        row = _request_in_scope(request_id, scope_user_ids)
        manager_rows = _manager_pool(scope_users)
        escalated_to_id = _safe_int(request.form.get("escalated_to_id"))
        if not escalated_to_id:
            raise ValueError("Eskalasyon için hedef kullanıcı seçin.")
        escalated_to = next((item for item in manager_rows if int(item.id) == int(escalated_to_id)), None)
        if not escalated_to:
            raise ValueError("Seçilen kullanıcı bu kapsamda uygun görünmüyor.")
        active_task = row.tasks.filter(PersonnelSelfServiceRequestTask.status.in_(["open", "in_progress"])).order_by(PersonnelSelfServiceRequestTask.id.desc()).first() if hasattr(row, "tasks") else None
        reason = _normalize_text(request.form.get("reason"), 255) or "SLA ve yönetici eskalasyonu"
        note = _normalize_text(request.form.get("note"), 2000) or None
        current_level = row.escalations.count() if hasattr(row, "escalations") else 0
        escalation = PersonnelSelfServiceRequestEscalation(
            request_id=row.id,
            task_id=getattr(active_task, "id", None),
            escalated_from_user_id=getattr(active_task, "assigned_to_id", None) or getattr(row, "current_handler_id", None),
            escalated_to_user_id=escalated_to.id,
            escalated_by_id=current_user.id,
            level=current_level + 1,
            status="open",
            reason=reason,
            note=note,
            escalated_at=utc_now(),
        )
        db.session.add(escalation)
        if active_task:
            active_task.assigned_to_id = escalated_to.id
            active_task.assigned_by_id = current_user.id
            active_task.status = "open" if active_task.status != "completed" else active_task.status
            active_task.note = ((active_task.note or "") + ("\n" if active_task.note else "") + f"Eskalasyon: {reason}" + (f" · {note}" if note else "")).strip()
            db.session.add(active_task)
        else:
            task = PersonnelSelfServiceRequestTask(
                request_id=row.id,
                assigned_to_id=escalated_to.id,
                assigned_by_id=current_user.id,
                task_type="escalation_review",
                title=f"Eskalasyon incelemesi: {row.title}",
                status="open",
                priority=getattr(row, "priority", None) or "high",
                due_at=_effective_due_at(row),
                note=reason + (f" · {note}" if note else ""),
                is_primary=False,
            )
            db.session.add(task)
        row.current_handler_id = escalated_to.id
        if (getattr(row, "status", None) or "draft") == "submitted":
            row.status = "in_review"
        row.last_action_by_id = current_user.id
        db.session.add(row)
        _write_request_log(row, action="escalated", from_status=getattr(row, "status", None), to_status=getattr(row, "status", None), note=f"Talep {_full_name(escalated_to)} kullanıcısına eskale edildi. {reason}" + (f" · {note}" if note else ""))
        db.session.commit()
        flash("Talep eskalasyon akışına alındı.", "success")
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(str(exc), "danger")
    return redirect(url_for("main.hr_personnel_request_analytics", scope=(hr_scope or {}).get("scope_mode")))