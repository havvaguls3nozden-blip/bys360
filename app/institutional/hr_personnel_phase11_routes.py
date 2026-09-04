from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_CHILD_IMPORT
# STATUS_SOURCE: app.institutional.routes LOADED_CHILD_ROUTE_MODULES
import logging
from datetime import date
from typing import Any

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import inspect

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import (
    PersonnelExitInterview,
    PersonnelLifecycleCase,
    PersonnelLifecycleTask,
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

from .hr_personnel_extension_routes import (
    _base_context,
    _full_name,
    _normalize_text,
    _parse_date,
    _safe_int,
    _scope_user_options,
)

logger = logging.getLogger(__name__)

LIFECYCLE_TYPE_LABELS = {
    "onboarding": "İşe Başlatma",
    "offboarding": "Ayrılış",
    "unit_change": "Birim Değişikliği",
    "return_to_work": "İşe Dönüş",
}
LIFECYCLE_STATUS_LABELS = {
    "draft": "Taslak",
    "in_progress": "İşlemde",
    "waiting": "Beklemede",
    "completed": "Tamamlandı",
    "cancelled": "İptal",
}
TASK_STATUS_LABELS = {
    "pending": "Bekliyor",
    "in_progress": "İşlemde",
    "completed": "Tamamlandı",
    "blocked": "Bloke",
}
SEPARATION_REASON_LABELS = {
    "emeklilik": "Emeklilik",
    "nakil": "Nakil",
    "istifa": "İstifa",
    "gorev_sonu": "Görev Sonu",
    "diger": "Diğer",
}


def _table_exists(table_name: str) -> bool:
    try:
        return table_name in set(inspect(db.engine).get_table_names())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_personnel_phase11_routes.py:61")
        return False


def _type_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return LIFECYCLE_TYPE_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return LIFECYCLE_STATUS_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _task_status_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return TASK_STATUS_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _reason_label(value: str | None) -> str:
    raw = (value or "").strip().lower()
    return SEPARATION_REASON_LABELS.get(raw, "Bilinmiyor" if raw else "-")


def _case_in_scope(case_id: int | None, scope_user_ids: set[int]) -> PersonnelLifecycleCase:
    if not case_id:
        raise ValueError("Yaşam döngüsü kaydı bulunamadı.")
    row = PersonnelLifecycleCase.query.filter(
        PersonnelLifecycleCase.id == int(case_id),
        PersonnelLifecycleCase.user_id.in_(list(scope_user_ids)),
    ).first()
    if not row:
        raise ValueError("Yaşam döngüsü kaydı bu kapsam içinde bulunamadı.")
    return row


def _task_in_scope(task_id: int | None, scope_user_ids: set[int]) -> PersonnelLifecycleTask:
    if not task_id:
        raise ValueError("Görev kaydı bulunamadı.")
    row = (
        PersonnelLifecycleTask.query
        .join(PersonnelLifecycleCase, PersonnelLifecycleCase.id == PersonnelLifecycleTask.case_id)
        .filter(
            PersonnelLifecycleTask.id == int(task_id),
            PersonnelLifecycleCase.user_id.in_(list(scope_user_ids)),
        )
        .first()
    )
    if not row:
        raise ValueError("Görev kaydı bu kapsam içinde bulunamadı.")
    return row


def _interview_in_scope(interview_id: int | None, scope_user_ids: set[int]) -> PersonnelExitInterview:
    if not interview_id:
        raise ValueError("Çıkış görüşmesi kaydı bulunamadı.")
    row = PersonnelExitInterview.query.filter(
        PersonnelExitInterview.id == int(interview_id),
        PersonnelExitInterview.user_id.in_(list(scope_user_ids)),
    ).first()
    if not row:
        raise ValueError("Çıkış görüşmesi kaydı bu kapsam içinde bulunamadı.")
    return row


def _progress(case: PersonnelLifecycleCase) -> int:
    tasks = list(case.tasks.order_by(PersonnelLifecycleTask.id.asc()).all()) if getattr(case, 'tasks', None) is not None else []
    if not tasks:
        return 0
    done = sum(1 for item in tasks if (item.status or '').strip().lower() == 'completed')
    return int(round((done / len(tasks)) * 100)) if tasks else 0


def _redirect_center(case_id: int | None = None, user_id: int | None = None, scope_mode: str | None = None):
    params: dict[str, Any] = {}
    scope_value = (scope_mode or request.form.get('scope') or request.args.get('scope') or '').strip()
    if scope_value:
        params['scope'] = scope_value
    if case_id:
        params['case_id'] = int(case_id)
    if user_id:
        params['user_id'] = int(user_id)
    return redirect(url_for('main.hr_personnel_lifecycle_center', **params))


@main_bp.route('/hr-management/personnel-operations/lifecycle')
@login_required
@manager_required
@menu_key_required('hr_leave_tracking')
def hr_personnel_lifecycle_center():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, selected_user = _base_context()
    lifecycle_ready = all(_table_exists(name) for name in ['personnel_lifecycle_cases', 'personnel_lifecycle_tasks'])
    selected_case = None
    case_rows: list[dict[str, object]] = []
    summary = {'open': 0, 'completed': 0, 'critical': 0, 'tasks': 0}
    if lifecycle_ready and scope_user_ids:
        edit_case_id = _safe_int(request.args.get('case_id'))
        if edit_case_id:
            selected_case = _case_in_scope(edit_case_id, scope_user_ids)
            selected_user = db.session.get(User, int(selected_case.user_id)) or selected_user
        q = PersonnelLifecycleCase.query.filter(PersonnelLifecycleCase.user_id.in_(list(scope_user_ids)))
        if selected_user:
            q = q.filter(PersonnelLifecycleCase.user_id == int(selected_user.id))
        rows = q.order_by(PersonnelLifecycleCase.created_at.desc(), PersonnelLifecycleCase.id.desc()).all()
        today = date.today()
        for row in rows:
            progress = _progress(row)
            task_rows = row.tasks.order_by(PersonnelLifecycleTask.id.asc()).all()
            summary['tasks'] += len(task_rows)
            status = (row.status or 'draft').strip().lower()
            if status == 'completed':
                summary['completed'] += 1
            else:
                summary['open'] += 1
                if row.target_date and row.target_date < today:
                    summary['critical'] += 1
            case_rows.append({
                'id': int(row.id),
                'title': row.title,
                'type_label': _type_label(row.lifecycle_type),
                'status': status,
                'status_label': _status_label(status),
                'priority': row.priority or 'normal',
                'start_date': row.start_date,
                'target_date': row.target_date,
                'progress': progress,
                'owner_name': _full_name(getattr(row, 'owner_user', None)),
                'task_count': len(task_rows),
                'completed_tasks': sum(1 for item in task_rows if (item.status or '').strip().lower() == 'completed'),
                'summary': row.summary or '',
            })
    task_rows_payload = []
    if selected_case is not None:
        for item in selected_case.tasks.order_by(PersonnelLifecycleTask.id.asc()).all():
            task_rows_payload.append({
                'id': int(item.id),
                'title': item.title,
                'category': item.category or 'genel',
                'status': item.status or 'pending',
                'status_label': _task_status_label(item.status),
                'assigned_to_name': _full_name(getattr(item, 'assigned_to', None)),
                'due_date': item.due_date,
                'note': item.note or '',
                'is_required': bool(item.is_required),
            })
    return safe_render(
        'hr_personnel_lifecycle_center.html',
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        lifecycle_ready=lifecycle_ready,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        selected_case=selected_case,
        lifecycle_summary=summary,
        lifecycle_rows=case_rows,
        lifecycle_task_rows=task_rows_payload,
        lifecycle_case_form_token=issue_form_token('hr_personnel_lifecycle_case_save', scope='hr_personnel_phase11'),
        lifecycle_task_form_token=issue_form_token('hr_personnel_lifecycle_task_save', scope='hr_personnel_phase11'),
        lifecycle_task_status_token=issue_form_token('hr_personnel_lifecycle_task_status', scope='hr_personnel_phase11'),
    )


@main_bp.route('/hr-management/personnel-operations/lifecycle/save', methods=['POST'])
@login_required
@manager_required
@menu_key_required('hr_leave_tracking')
def hr_personnel_lifecycle_case_save():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    if not all(_table_exists(name) for name in ['personnel_lifecycle_cases', 'personnel_lifecycle_tasks']):
        flash('Yaşam döngüsü tabloları henüz hazır değil.', 'warning')
        return _redirect_center(scope_mode=selected_scope_mode)
    try:
        submitted_token = (request.form.get('form_token') or '').strip()
        if not consume_form_token('hr_personnel_lifecycle_case_save', submitted_token, scope='hr_personnel_phase11'):
            raise ValueError('Form güvenlik anahtarı doğrulanamadı.')
        user_id = _safe_int(request.form.get('user_id'))
        if not user_id or user_id not in scope_user_ids:
            raise ValueError('Seçilen personel bu kapsam içinde görünmüyor.')
        row = _case_in_scope(_safe_int(request.form.get('case_id')), scope_user_ids) if _safe_int(request.form.get('case_id')) else PersonnelLifecycleCase(user_id=int(user_id), created_by_id=getattr(current_user, 'id', None))
        row.organization_unit_id = getattr(db.session.get(User, int(user_id)), 'organization_unit_id', None)
        row.owner_user_id = _safe_int(request.form.get('owner_user_id')) or getattr(current_user, 'id', None)
        row.coordinator_user_id = _safe_int(request.form.get('coordinator_user_id'))
        row.lifecycle_type = _normalize_text(request.form.get('lifecycle_type') or 'onboarding', 50).lower() or 'onboarding'
        row.title = _normalize_text(request.form.get('title'), 255) or 'Yaşam döngüsü kaydı'
        row.status = _normalize_text(request.form.get('status') or 'draft', 30).lower() or 'draft'
        row.priority = _normalize_text(request.form.get('priority') or 'normal', 20).lower() or 'normal'
        row.start_date = _parse_date(request.form.get('start_date'))
        row.target_date = _parse_date(request.form.get('target_date'))
        row.decision_no = _normalize_text(request.form.get('decision_no'), 120) or None
        row.summary = (request.form.get('summary') or '').strip() or None
        if row.status == 'completed' and not row.completed_at:
            row.completed_at = utc_now()
        elif row.status != 'completed':
            row.completed_at = None
        db.session.add(row)
        db.session.commit()
        flash('Yaşam döngüsü kaydı kaydedildi.', 'success')
        return _redirect_center(case_id=row.id, user_id=user_id, scope_mode=selected_scope_mode)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(str(exc), 'danger')
        return _redirect_center(user_id=_safe_int(request.form.get('user_id')), scope_mode=selected_scope_mode)


@main_bp.route('/hr-management/personnel-operations/lifecycle/task/save', methods=['POST'])
@login_required
@manager_required
@menu_key_required('hr_leave_tracking')
def hr_personnel_lifecycle_task_save():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    if not _table_exists('personnel_lifecycle_tasks'):
        flash('Görev tabloları henüz hazır değil.', 'warning')
        return _redirect_center(scope_mode=selected_scope_mode)
    try:
        submitted_token = (request.form.get('form_token') or '').strip()
        if not consume_form_token('hr_personnel_lifecycle_task_save', submitted_token, scope='hr_personnel_phase11'):
            raise ValueError('Form güvenlik anahtarı doğrulanamadı.')
        case_row = _case_in_scope(_safe_int(request.form.get('case_id')), scope_user_ids)
        row = PersonnelLifecycleTask(case_id=int(case_row.id), created_by_id=getattr(current_user, 'id', None))
        row.assigned_to_id = _safe_int(request.form.get('assigned_to_id'))
        row.category = _normalize_text(request.form.get('category') or 'genel', 50).lower() or 'genel'
        row.title = _normalize_text(request.form.get('title'), 255) or 'Görev'
        row.status = _normalize_text(request.form.get('status') or 'pending', 30).lower() or 'pending'
        row.due_date = _parse_date(request.form.get('due_date'))
        row.is_required = str(request.form.get('is_required') or '1').strip().lower() in {'1', 'true', 'on', 'yes', 'evet'}
        row.note = (request.form.get('note') or '').strip() or None
        if row.status == 'completed':
            row.completed_at = utc_now()
        db.session.add(row)
        db.session.commit()
        flash('Yaşam döngüsü görevi eklendi.', 'success')
        return _redirect_center(case_id=case_row.id, user_id=case_row.user_id, scope_mode=selected_scope_mode)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(str(exc), 'danger')
        return _redirect_center(case_id=_safe_int(request.form.get('case_id')), scope_mode=selected_scope_mode)


@main_bp.route('/hr-management/personnel-operations/lifecycle/task/status', methods=['POST'])
@login_required
@manager_required
@menu_key_required('hr_leave_tracking')
def hr_personnel_lifecycle_task_status():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    try:
        submitted_token = (request.form.get('form_token') or '').strip()
        if not consume_form_token('hr_personnel_lifecycle_task_status', submitted_token, scope='hr_personnel_phase11'):
            raise ValueError('Form güvenlik anahtarı doğrulanamadı.')
        row = _task_in_scope(_safe_int(request.form.get('task_id')), scope_user_ids)
        row.status = _normalize_text(request.form.get('status') or 'pending', 30).lower() or 'pending'
        row.completed_at = utc_now() if row.status == 'completed' else None
        db.session.add(row)
        db.session.commit()
        flash('Görev durumu güncellendi.', 'success')
        return _redirect_center(case_id=row.case_id, user_id=getattr(row.case, 'user_id', None), scope_mode=selected_scope_mode)
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(str(exc), 'danger')
        return _redirect_center(scope_mode=selected_scope_mode)


@main_bp.route('/hr-management/personnel-operations/lifecycle-board')
@login_required
@manager_required
@menu_key_required('hr_leave_tracking')
def hr_personnel_lifecycle_board():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    board_ready = _table_exists('personnel_lifecycle_cases')
    status_columns = ['draft', 'in_progress', 'waiting', 'completed']
    board: dict[str, list[dict[str, Any]]] = {key: [] for key in status_columns}
    if board_ready and scope_user_ids:
        rows = (
            PersonnelLifecycleCase.query
            .filter(PersonnelLifecycleCase.user_id.in_(list(scope_user_ids)))
            .order_by(PersonnelLifecycleCase.target_date.asc().nullslast(), PersonnelLifecycleCase.id.desc())
            .all()
        )
        for row in rows:
            status = (row.status or 'draft').strip().lower()
            board.setdefault(status, [])
            board[status].append({
                'id': int(row.id),
                'user_name': _full_name(getattr(row, 'user', None)),
                'title': row.title,
                'type_label': _type_label(row.lifecycle_type),
                'target_date': row.target_date,
                'progress': _progress(row),
                'owner_name': _full_name(getattr(row, 'owner_user', None)),
            })
    return safe_render(
        'hr_personnel_lifecycle_board.html',
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        board_ready=board_ready,
        lifecycle_board=board,
        status_labels={key: _status_label(key) for key in status_columns},
    )


@main_bp.route('/hr-management/personnel-operations/exit-interviews')
@login_required
@manager_required
@menu_key_required('hr_leave_tracking')
def hr_personnel_exit_interviews():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, selected_user = _base_context()
    interviews_ready = all(_table_exists(name) for name in ['personnel_exit_interviews', 'personnel_lifecycle_cases'])
    edit_interview = None
    rows_payload = []
    if interviews_ready and scope_user_ids:
        edit_id = _safe_int(request.args.get('interview_id'))
        if edit_id:
            edit_interview = _interview_in_scope(edit_id, scope_user_ids)
            selected_user = db.session.get(User, int(edit_interview.user_id)) or selected_user
        q = PersonnelExitInterview.query.filter(PersonnelExitInterview.user_id.in_(list(scope_user_ids)))
        if selected_user:
            q = q.filter(PersonnelExitInterview.user_id == int(selected_user.id))
        rows = q.order_by(PersonnelExitInterview.interview_date.desc(), PersonnelExitInterview.id.desc()).all()
        for row in rows:
            rows_payload.append({
                'id': int(row.id),
                'user_id': int(row.user_id),
                'user_name': _full_name(getattr(row, 'user', None)),
                'interview_date': row.interview_date,
                'separation_reason_label': _reason_label(row.separation_reason),
                'satisfaction_score': row.satisfaction_score,
                'would_rehire': bool(row.would_rehire),
                'interviewer_name': _full_name(getattr(row, 'interviewed_by', None)),
                'summary': row.summary or '',
            })
    available_cases = []
    if interviews_ready and selected_user:
        case_rows = PersonnelLifecycleCase.query.filter_by(user_id=int(selected_user.id)).order_by(PersonnelLifecycleCase.created_at.desc()).all()
        available_cases = [{'id': int(row.id), 'title': row.title} for row in case_rows if (row.lifecycle_type or '').strip().lower() == 'offboarding']
    return safe_render(
        'hr_personnel_exit_interviews.html',
        hr_scope=hr_scope,
        selected_scope_mode=selected_scope_mode,
        interviews_ready=interviews_ready,
        scope_user_options=_scope_user_options(scope_users),
        selected_user=selected_user,
        selected_user_id=int(selected_user.id) if selected_user else None,
        selected_interview=edit_interview,
        interview_rows=rows_payload,
        available_cases=available_cases,
        exit_interview_form_token=issue_form_token('hr_personnel_exit_interview_save', scope='hr_personnel_phase11'),
    )


@main_bp.route('/hr-management/personnel-operations/exit-interviews/save', methods=['POST'])
@login_required
@manager_required
@menu_key_required('hr_leave_tracking')
def hr_personnel_exit_interview_save():
    hr_scope, scope_users, scope_user_ids, selected_scope_mode, _selected_user = _base_context()
    try:
        submitted_token = (request.form.get('form_token') or '').strip()
        if not consume_form_token('hr_personnel_exit_interview_save', submitted_token, scope='hr_personnel_phase11'):
            raise ValueError('Form güvenlik anahtarı doğrulanamadı.')
        user_id = _safe_int(request.form.get('user_id'))
        if not user_id or user_id not in scope_user_ids:
            raise ValueError('Seçilen personel bu kapsam içinde görünmüyor.')
        edit_id = _safe_int(request.form.get('interview_id'))
        row = _interview_in_scope(edit_id, scope_user_ids) if edit_id else PersonnelExitInterview(user_id=int(user_id), interviewed_by_id=getattr(current_user, 'id', None))
        row.lifecycle_case_id = _safe_int(request.form.get('lifecycle_case_id'))
        row.interview_date = _parse_date(request.form.get('interview_date')) or date.today()
        row.separation_reason = _normalize_text(request.form.get('separation_reason') or 'diger', 50).lower() or 'diger'
        try:
            row.satisfaction_score = int(request.form.get('satisfaction_score') or 0) or None
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/institutional/hr_personnel_phase11_routes.py:430")
            row.satisfaction_score = None
        row.would_rehire = str(request.form.get('would_rehire') or '1').strip().lower() in {'1', 'true', 'on', 'yes', 'evet'}
        row.summary = (request.form.get('summary') or '').strip() or None
        row.risk_flags = (request.form.get('risk_flags') or '').strip() or None
        row.action_note = (request.form.get('action_note') or '').strip() or None
        db.session.add(row)
        db.session.commit()
        flash('Çıkış görüşmesi kaydedildi.', 'success')
        return redirect(url_for('main.hr_personnel_exit_interviews', scope=selected_scope_mode, user_id=user_id))
    except Exception as exc:
        logger.exception("Beklenmeyen hata: %s", exc)
        safe_db_rollback()
        flash(str(exc), 'danger')
        return redirect(url_for('main.hr_personnel_exit_interviews', scope=selected_scope_mode, user_id=_safe_int(request.form.get('user_id'))))
