from __future__ import annotations

from app.core.datetime_utils import utc_now
import csv
import io
from datetime import datetime

from flask import Response, flash, redirect, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import PersonnelSelfServiceRequest, PersonnelSelfServiceRequestTask, User
from app.route_registry import main_bp
from app.route_support import consume_form_token, issue_form_token, manager_required, menu_key_required, safe_db_rollback, safe_render

from .hr_personnel_operations_routes import (
    _current_scope_bundle,
    _full_name,
    _normalize_text,
    _redirect_request_review,
    _request_in_scope,
    _request_priority_label,
    _request_status_label,
    _request_type_label,
    _safe_int,
    _sla_payload,
    _table_exists,
    _write_request_log,
)

TASK_STATUS_LABELS = {
    "open": "Açık",
    "in_progress": "Çalışılıyor",
    "completed": "Tamamlandı",
    "cancelled": "İptal",
}


def _task_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return TASK_STATUS_LABELS.get(raw, raw.replace("_", " ").title() if raw else "-")


def _manager_pool(scope_users: list[User]) -> list[User]:
    result: list[User] = []
    seen: set[int] = set()
    for user in scope_users:
        role = (getattr(user, "role", "") or "").strip().lower()
        if role in {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "birim_amiri"}:
            if int(user.id) not in seen:
                seen.add(int(user.id))
                result.append(user)
    if getattr(current_user, "id", None) and int(current_user.id) not in seen:
        result.append(current_user)
    result.sort(key=lambda item: (_full_name(item).lower(), int(getattr(item, "id", 0))))
    return result


def _task_row_payload(row: PersonnelSelfServiceRequestTask) -> dict[str, object]:
    req = getattr(row, "request", None)
    sla = _sla_payload(req)
    return {
        "id": int(row.id),
        "request_id": int(row.request_id),
        "title": row.title or (getattr(req, "title", None) or "Talep görevi"),
        "task_type": row.task_type or "review",
        "status": row.status or "open",
        "status_label": _task_status_label(row.status),
        "priority": row.priority or (getattr(req, "priority", None) or "normal"),
        "priority_label": _request_priority_label(row.priority or getattr(req, "priority", None)),
        "assigned_to_name": _full_name(getattr(row, "assigned_to", None)),
        "assigned_by_name": _full_name(getattr(row, "assigned_by", None)),
        "assigned_at": getattr(row, "created_at", None),
        "due_at": getattr(row, "due_at", None),
        "started_at": getattr(row, "started_at", None),
        "completed_at": getattr(row, "completed_at", None),
        "note": row.note or "",
        "completion_note": row.completion_note or "",
        "sla": sla,
        "request_title": getattr(req, "title", None) or "Talep",
        "request_status": getattr(req, "status", None) or "draft",
        "request_status_label": _request_status_label(getattr(req, "status", None)),
        "request_type_label": _request_type_label(getattr(req, "request_type", None)),
        "request_user_name": _full_name(getattr(req, "user", None)),
    }


def _task_rows(scope_user_ids: set[int]) -> list[dict[str, object]]:
    if not _table_exists("personnel_self_service_request_tasks"):
        return []
    rows = (
        PersonnelSelfServiceRequestTask.query
        .join(PersonnelSelfServiceRequestTask.request)
        .filter(PersonnelSelfServiceRequestTask.request.has(PersonnelSelfServiceRequest.user_id.in_(list(scope_user_ids))))
        .order_by(PersonnelSelfServiceRequestTask.completed_at.asc().nullsfirst(), PersonnelSelfServiceRequestTask.due_at.asc().nullslast(), PersonnelSelfServiceRequestTask.id.desc())
        .all()
    )
    return [_task_row_payload(row) for row in rows]


def _request_report_rows(scope_user_ids: set[int]) -> list[dict[str, object]]:
    if not _table_exists("personnel_self_service_requests"):
        return []
    from app.models.hr_models import PersonnelSelfServiceRequest
    rows = (
        PersonnelSelfServiceRequest.query
        .filter(PersonnelSelfServiceRequest.user_id.in_(list(scope_user_ids)))
        .order_by(PersonnelSelfServiceRequest.created_at.desc(), PersonnelSelfServiceRequest.id.desc())
        .all()
    )
    result = []
    for row in rows:
        tasks = row.tasks.order_by(PersonnelSelfServiceRequestTask.id.desc()).all() if hasattr(row, "tasks") else []
        open_tasks = [item for item in tasks if (getattr(item, "status", None) or "open") not in {"completed", "cancelled"}]
        primary_task = open_tasks[0] if open_tasks else (tasks[0] if tasks else None)
        sla = _sla_payload(row)
        result.append({
            "id": int(row.id),
            "created_at": getattr(row, "created_at", None),
            "user_name": _full_name(getattr(row, "user", None)),
            "title": row.title,
            "request_type_label": _request_type_label(getattr(row, "request_type", None)),
            "priority_label": _request_priority_label(getattr(row, "priority", None)),
            "status": getattr(row, "status", None) or "draft",
            "status_label": _request_status_label(getattr(row, "status", None)),
            "handler_name": _full_name(getattr(row, "current_handler", None)),
            "task_count": len(tasks),
            "open_task_count": len(open_tasks),
            "primary_task_status_label": _task_status_label(getattr(primary_task, "status", None)) if primary_task else "-",
            "primary_task_owner": _full_name(getattr(primary_task, "assigned_to", None)) if primary_task else "-",
            "sla": sla,
            "decision_note": getattr(row, "decision_note", None) or "",
        })
    return result


def _task_dashboard_payload(hr_scope: dict[str, object], scope_users: list[User], scope_user_ids: set[int]) -> dict[str, object]:
    rows = _task_rows(scope_user_ids)
    manager_pool = _manager_pool(scope_users)
    my_task_count = sum(1 for row in rows if row.get("assigned_to_name") == _full_name(current_user) and row.get("status") not in {"completed", "cancelled"})
    summary = {
        "open": sum(1 for row in rows if row.get("status") == "open"),
        "in_progress": sum(1 for row in rows if row.get("status") == "in_progress"),
        "completed": sum(1 for row in rows if row.get("status") == "completed"),
        "overdue": sum(1 for row in rows if (row.get("sla") or {}).get("days_remaining", 999999) < 0 and row.get("status") not in {"completed", "cancelled"}),
        "my_open": my_task_count,
        "unassigned_requests": 0,
    }
    if _table_exists("personnel_self_service_requests"):
        from app.models.hr_models import PersonnelSelfServiceRequest
        request_ids_with_tasks = {int(row["request_id"]) for row in rows}
        all_requests = PersonnelSelfServiceRequest.query.filter(PersonnelSelfServiceRequest.user_id.in_(list(scope_user_ids))).all()
        summary["unassigned_requests"] = sum(
            1 for req in all_requests if int(req.id) not in request_ids_with_tasks and (getattr(req, "status", None) or "draft") in {"submitted", "in_review", "returned"}
        )
    selected_request = None
    selected_request_id = _safe_int(request.args.get("request_id"))
    if selected_request_id:
        try:
            selected_request = _request_in_scope(selected_request_id, scope_user_ids)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_request_task_routes.py:163")
            selected_request = None
    return {
        "hr_scope": hr_scope,
        "selected_scope_mode": (hr_scope or {}).get("scope_mode") or "personal",
        "scope_label": (hr_scope or {}).get("scope_label") or "Kapsam",
        "task_rows": rows,
        "task_summary": summary,
        "manager_rows": manager_pool,
        "selected_request": selected_request,
        "task_assign_token": issue_form_token("hr_personnel_request_task_assign", scope="hr_personnel_request_tasks"),
        "task_complete_token": issue_form_token("hr_personnel_request_task_complete", scope="hr_personnel_request_tasks"),
    }


def _request_reports_payload(hr_scope: dict[str, object], scope_user_ids: set[int]) -> dict[str, object]:
    rows = _request_report_rows(scope_user_ids)
    return {
        "hr_scope": hr_scope,
        "selected_scope_mode": (hr_scope or {}).get("scope_mode") or "personal",
        "scope_label": (hr_scope or {}).get("scope_label") or "Kapsam",
        "report_rows": rows,
        "report_summary": {
            "total": len(rows),
            "open": sum(1 for row in rows if row.get("status") in {"submitted", "in_review", "returned"}),
            "approved": sum(1 for row in rows if row.get("status") == "approved"),
            "rejected": sum(1 for row in rows if row.get("status") == "rejected"),
            "overdue": sum(1 for row in rows if (row.get("sla") or {}).get("days_remaining", 999999) < 0 and row.get("status") not in {"approved", "rejected"}),
        },
    }


@main_bp.route("/hr-management/personnel-operations/request-tasks")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_request_tasks():
    hr_scope, scope_users, scope_user_ids = _current_scope_bundle()
    payload = _task_dashboard_payload(hr_scope, scope_users, scope_user_ids)
    return safe_render("hr_personnel_request_tasks.html", **payload)


@main_bp.route("/hr-management/personnel-operations/request/<int:request_id>/assign", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_request_task_assign(request_id: int):
    hr_scope, scope_users, scope_user_ids = _current_scope_bundle()
    if not consume_form_token("hr_personnel_request_task_assign", request.form.get("form_token"), scope="hr_personnel_request_tasks"):
        flash("Görev atama güvenlik doğrulaması başarısız oldu.", "danger")
        return redirect(url_for("main.hr_personnel_request_tasks", scope=(hr_scope or {}).get("scope_mode"), request_id=request_id))
    try:
        row = _request_in_scope(request_id, scope_user_ids)
        assignee_id = _safe_int(request.form.get("assigned_to_id"))
        if not assignee_id:
            raise ValueError("Görev atamak için bir kullanıcı seçin.")
        assignee = next((item for item in _manager_pool(scope_users) if int(item.id) == int(assignee_id)), None)
        if not assignee:
            raise ValueError("Seçilen görev sahibi bu kapsam içinde uygun görünmüyor.")
        note = _normalize_text(request.form.get("note"), 2000) or None
        due_at = getattr(row, "due_at", None)
        title = _normalize_text(request.form.get("task_title") or f"Talep inceleme: {getattr(row, 'title', 'Talep')}", 255)

        active_task = None
        if hasattr(row, "tasks"):
            active_task = row.tasks.filter(PersonnelSelfServiceRequestTask.status.in_(["open", "in_progress"])).order_by(PersonnelSelfServiceRequestTask.id.desc()).first()
        if active_task:
            active_task.assigned_to_id = assignee.id
            active_task.assigned_by_id = current_user.id
            active_task.title = title
            active_task.priority = getattr(row, "priority", None) or "normal"
            active_task.note = note
            active_task.due_at = due_at
            active_task.status = "open" if active_task.status == "open" else active_task.status
            db.session.add(active_task)
        else:
            active_task = PersonnelSelfServiceRequestTask(
                request_id=row.id,
                assigned_to_id=assignee.id,
                assigned_by_id=current_user.id,
                task_type="review",
                title=title,
                status="open",
                priority=getattr(row, "priority", None) or "normal",
                due_at=due_at,
                note=note,
                is_primary=True,
            )
            db.session.add(active_task)
        previous_status = (getattr(row, "status", None) or "submitted").strip().lower()
        row.current_handler_id = assignee.id
        if previous_status == "submitted":
            row.status = "in_review"
        row.last_action_by_id = current_user.id
        db.session.add(row)
        _write_request_log(row, action="assign", from_status=previous_status, to_status=row.status, note=f"Görev atandı: {_full_name(assignee)}" + (f" · {note}" if note else ""))
        db.session.commit()
        flash("Talep görevi atandı.", "success")
    except Exception as exc:
        safe_db_rollback()
        flash(str(exc), "danger")
    return redirect(url_for("main.hr_personnel_request_tasks", scope=(hr_scope or {}).get("scope_mode"), request_id=request_id))


@main_bp.route("/hr-management/personnel-operations/request-task/<int:task_id>/complete", methods=["POST"])
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_request_task_complete(task_id: int):
    hr_scope, _, scope_user_ids = _current_scope_bundle()
    if not consume_form_token("hr_personnel_request_task_complete", request.form.get("form_token"), scope="hr_personnel_request_tasks"):
        flash("Görev güncelleme güvenlik doğrulaması başarısız oldu.", "danger")
        return redirect(url_for("main.hr_personnel_request_tasks", scope=(hr_scope or {}).get("scope_mode")))
    try:
        row = PersonnelSelfServiceRequestTask.query.get_or_404(task_id)
        req = getattr(row, "request", None)
        if not req or int(getattr(req, "user_id", 0)) not in scope_user_ids:
            raise ValueError("Görev bu kapsam içinde görünmüyor.")
        action = _normalize_text(request.form.get("task_action") or "complete", 30).lower() or "complete"
        note = _normalize_text(request.form.get("completion_note"), 2000) or None
        previous_status = (getattr(row, "status", None) or "open").strip().lower()
        if action == "start":
            row.status = "in_progress"
            row.started_at = row.started_at or utc_now()
        elif action == "cancel":
            row.status = "cancelled"
            row.completed_at = utc_now()
        else:
            row.status = "completed"
            row.completed_at = utc_now()
        row.completion_note = note
        db.session.add(row)
        if req:
            req.last_action_by_id = current_user.id
            if action == "complete" and (getattr(req, "status", None) or "submitted") not in {"approved", "rejected", "returned"}:
                req.status = "in_review"
            db.session.add(req)
            _write_request_log(req, action=f"task_{action}", from_status=getattr(req, "status", None), to_status=getattr(req, "status", None), note=f"Görev durumu: {previous_status} → {row.status}" + (f" · {note}" if note else ""))
        db.session.commit()
        flash("Görev durumu güncellendi.", "success")
    except Exception as exc:
        safe_db_rollback()
        flash(str(exc), "danger")
    return redirect(url_for("main.hr_personnel_request_tasks", scope=(hr_scope or {}).get("scope_mode"), request_id=_safe_int(request.form.get("request_id"))))


@main_bp.route("/hr-management/personnel-operations/request-reports")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_request_reports():
    hr_scope, _, scope_user_ids = _current_scope_bundle()
    payload = _request_reports_payload(hr_scope, scope_user_ids)
    return safe_render("hr_personnel_request_reports.html", **payload)


@main_bp.route("/hr-management/personnel-operations/request-reports/export")
@login_required
@manager_required
@menu_key_required("hr_leave_tracking")
def hr_personnel_request_reports_export():
    hr_scope, _, scope_user_ids = _current_scope_bundle()
    payload = _request_reports_payload(hr_scope, scope_user_ids)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Talep ID", "Tarih", "Personel", "Başlık", "Tür", "Öncelik", "Durum", "Sorumlu", "Açık Görev", "Toplam Görev", "SLA", "Karar Notu"])
    for row in payload["report_rows"]:
        writer.writerow([
            row["id"],
            row["created_at"].strftime("%d.%m.%Y %H:%M") if row.get("created_at") else "",
            row["user_name"],
            row["title"],
            row["request_type_label"],
            row["priority_label"],
            row["status_label"],
            row["primary_task_owner"],
            row["open_task_count"],
            row["task_count"],
            (row.get("sla") or {}).get("label", "Takipsiz"),
            row["decision_note"],
        ])
    csv_bytes = output.getvalue().encode("utf-8-sig")
    filename = f"hr_talep_raporu_{utc_now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(csv_bytes, mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": f"attachment; filename={filename}"})
