from __future__ import annotations



from app.services.mail_core import *  # noqa: F401,F403

def _build_mail_common_context() -> dict[str, Any]:
    settings = get_smtp_settings()
    return {
        "login_url": f"{settings['app_base_url']}/login",
        "app_name": settings["app_name"],
        "institution_name": settings["institution_name"],
    }


def build_assignment_reminder_email(manager: User, period: PerformancePeriod, pending_count: int) -> tuple[str, str]:
    template = get_mail_template_content(PERFORMANCE_REMINDER_MAIL_TYPE)
    detail = {}
    if getattr(manager, 'id', None) and getattr(period, 'id', None):
        detail = next(
            (
                row for row in _collect_pending_assignment_manager_states(
                    period.id,
                    reminder_interval_hours=REMINDER_COOLDOWN_HOURS,
                )
                if getattr(row.get('manager'), 'id', None) == getattr(manager, 'id', None)
            ),
            {},
        )
    context = {
        **_build_mail_common_context(),
        "manager_name": _manager_display_name(manager) or "Yönetici",
        "period_title": getattr(period, "title", "-") or "-",
        "pending_count": int(pending_count or 0),
        "level_breakdown": detail.get('level_breakdown') or '-',
        "overdue_count": int(detail.get('overdue_count') or 0),
        "due_soon_count": int(detail.get('due_soon_count') or 0),
        "oldest_pending_days": int(detail.get('oldest_pending_days') or 0),
        "employee_list": detail.get('employee_list') or '-',
    }
    subject = _render_text_template(template["subject"], context)
    body = _render_text_template(template["body"], context)
    return subject, body


def _pending_assignment_statuses() -> tuple[str, ...]:
    return ("bekliyor", "atandi", "kismen_tamamlandi", "taslak")


def get_pending_assignment_managers(period_id: int) -> list[dict[str, Any]]:
    rows = (
        EvaluationAssignment.query
        .filter(
            EvaluationAssignment.period_id == period_id,
            EvaluationAssignment.status.in_(_pending_assignment_statuses()),
        )
        .all()
    )

    grouped: dict[int, dict[str, Any]] = {}
    for assignment in rows:
        manager = assignment.evaluator
        email = _normalize_email_address(getattr(manager, "email", "") or "") if manager else ""
        if not manager or not email:
            continue
        bucket = grouped.setdefault(
            manager.id,
            {
                "manager": manager,
                "pending_count": 0,
                "assignment_ids": [],
            },
        )
        bucket["pending_count"] += 1
        bucket["assignment_ids"].append(assignment.id)

    return list(grouped.values())


def get_last_assignment_reminder(period_id: int, manager_id: int, *, success_only: bool = False) -> MailLog | None:
    query = (
        MailLog.query
        .filter(
            MailLog.mail_type == PERFORMANCE_REMINDER_MAIL_TYPE,
            MailLog.related_period_id == period_id,
            MailLog.related_user_id == manager_id,
        )
    )
    if success_only:
        query = query.filter(MailLog.is_success.is_(True))
    return query.order_by(MailLog.sent_at.desc(), MailLog.id.desc()).first()


def _collect_pending_assignment_manager_states(period_id: int, *, reminder_interval_hours: int = REMINDER_COOLDOWN_HOURS) -> list[dict[str, Any]]:
    assignments = (
        EvaluationAssignment.query
        .filter(
            EvaluationAssignment.period_id == period_id,
            EvaluationAssignment.status.in_(_pending_assignment_statuses()),
        )
        .order_by(EvaluationAssignment.due_date.asc().nulls_last(), EvaluationAssignment.assigned_at.asc(), EvaluationAssignment.id.asc())
        .all()
    )

    grouped: dict[str, dict[str, Any]] = {}
    for assignment in assignments:
        manager = assignment.evaluator
        if not manager:
            continue
        key = str(getattr(manager, 'id', None) or assignment.evaluator_id)
        bucket = grouped.setdefault(
            key,
            {
                'manager': manager,
                'assignments': [],
            },
        )
        bucket['assignments'].append(assignment)

    now = utc_now()
    cooldown = timedelta(hours=max(int(reminder_interval_hours or REMINDER_COOLDOWN_HOURS), 1))
    rows: list[dict[str, Any]] = []

    for bucket in grouped.values():
        manager = bucket['manager']
        manager_assignments = bucket['assignments']
        email = _normalize_email_address(getattr(manager, 'email', '') or '')
        level_counter: Counter[int] = Counter()
        overdue_count = 0
        due_soon_count = 0
        oldest_assigned_at = None
        employee_rows: list[dict[str, Any]] = []
        seen_employees: set[int] = set()

        for assignment in manager_assignments:
            level_counter[int(getattr(assignment, 'manager_level', 0) or 0)] += 1
            if getattr(assignment, 'is_overdue', False):
                overdue_count += 1
            elif getattr(assignment, 'is_due_soon', False):
                due_soon_count += 1
            assigned_at = getattr(assignment, 'assigned_at', None)
            if assigned_at and (oldest_assigned_at is None or assigned_at < oldest_assigned_at):
                oldest_assigned_at = assigned_at
            employee = getattr(assignment, 'employee', None)
            employee_id = getattr(employee, 'id', None)
            if employee_id and employee_id in seen_employees:
                continue
            if employee_id:
                seen_employees.add(employee_id)
            employee_rows.append(
                {
                    'employee_id': employee_id,
                    'employee_name': _employee_display_name(employee),
                    'manager_level': getattr(assignment, 'manager_level', None),
                    'is_overdue': bool(getattr(assignment, 'is_overdue', False)),
                    'is_due_soon': bool(getattr(assignment, 'is_due_soon', False)),
                    'due_date': getattr(assignment, 'due_date', None),
                }
            )

        level_breakdown = ' · '.join(
            f"{_manager_level_label(level)}: {count}" for level, count in sorted(level_counter.items(), key=lambda item: item[0]) if level
        ) or '-'

        preview_names = []
        for row in employee_rows[:5]:
            flags = []
            if row['is_overdue']:
                flags.append('gecikmiş')
            elif row['is_due_soon']:
                flags.append('yaklaşan')
            suffix = f" [{', '.join(flags)}]" if flags else ''
            preview_names.append(f"{row['employee_name']} ({_manager_level_label(row['manager_level'])}){suffix}")
        if len(employee_rows) > 5:
            preview_names.append(f"+{len(employee_rows) - 5} kişi daha")
        employee_preview = ', '.join(preview_names) or '-'

        employee_list = '\n'.join(
            f"- {row['employee_name']} | {_manager_level_label(row['manager_level'])}" + (
                " | gecikmiş" if row['is_overdue'] else (" | yaklaşan" if row['is_due_soon'] else "")
            )
            for row in employee_rows[:12]
        )
        if len(employee_rows) > 12:
            employee_list += f"\n- +{len(employee_rows) - 12} kişi daha"
        employee_list = employee_list or '-'

        oldest_pending_days = 0
        if oldest_assigned_at:
            oldest_pending_days = max(int((now - oldest_assigned_at).total_seconds() // 86400), 0)

        last_success_log = get_last_assignment_reminder(period_id, manager.id, success_only=True)
        last_attempt_log = get_last_assignment_reminder(period_id, manager.id, success_only=False)
        last_reminder_at = getattr(last_success_log, 'sent_at', None)
        next_allowed_at = (last_reminder_at + cooldown) if last_reminder_at else None
        can_send_now = bool(email) and (not next_allowed_at or now >= next_allowed_at)

        if not email:
            send_status = 'email_missing'
            send_block_reason = 'Yönetici için geçerli e-posta adresi tanımlı değil.'
        elif can_send_now:
            send_status = 'eligible'
            send_block_reason = None
        else:
            send_status = 'cooldown'
            send_block_reason = f"Son başarılı hatırlatmadan sonra {reminder_interval_hours} saat dolmadan tekrar gönderilmez."

        rows.append(
            {
                'manager': manager,
                'email': email or (getattr(manager, 'email', None) or ''),
                'email_valid': bool(email),
                'count': len(manager_assignments),
                'assignment_ids': [assignment.id for assignment in manager_assignments],
                'assignment_rows': manager_assignments,
                'level_breakdown': level_breakdown,
                'overdue_count': overdue_count,
                'due_soon_count': due_soon_count,
                'employee_preview': employee_preview,
                'employee_list': employee_list,
                'employee_total': len(employee_rows),
                'oldest_assigned_at': oldest_assigned_at,
                'oldest_pending_days': oldest_pending_days,
                'last_reminder_at': last_reminder_at,
                'last_attempt_at': getattr(last_attempt_log, 'sent_at', None),
                'last_attempt_success': bool(getattr(last_attempt_log, 'is_success', False)) if last_attempt_log else None,
                'next_allowed_at': next_allowed_at,
                'can_send_now': can_send_now,
                'send_status': send_status,
                'send_block_reason': send_block_reason,
            }
        )

    rows.sort(
        key=lambda row: (
            0 if row['send_status'] == 'eligible' else 1,
            -int(row.get('overdue_count') or 0),
            -(int(row.get('count') or 0)),
            (_manager_display_name(row.get('manager')) or '').lower(),
        )
    )
    return rows


def build_pending_assignment_manager_dashboard(period_id: int, *, reminder_interval_hours: int = REMINDER_COOLDOWN_HOURS) -> dict[str, Any]:
    all_rows = _collect_pending_assignment_manager_states(period_id, reminder_interval_hours=reminder_interval_hours)
    eligible_rows = [row for row in all_rows if row.get('email_valid')]
    blocked_rows = [row for row in all_rows if row.get('send_status') != 'eligible']
    return {
        'all_rows': all_rows,
        'eligible_rows': eligible_rows,
        'blocked_rows': blocked_rows,
        'missing_email_rows': [row for row in all_rows if row.get('send_status') == 'email_missing'],
        'cooldown_rows': [row for row in all_rows if row.get('send_status') == 'cooldown'],
        'total_manager_count': len(all_rows),
        'eligible_manager_count': len([row for row in all_rows if row.get('send_status') == 'eligible']),
        'blocked_manager_count': len(blocked_rows),
        'missing_email_count': len([row for row in all_rows if row.get('send_status') == 'email_missing']),
        'cooldown_count': len([row for row in all_rows if row.get('send_status') == 'cooldown']),
        'total_pending': sum(int(row.get('count') or 0) for row in all_rows),
        'overdue_total': sum(int(row.get('overdue_count') or 0) for row in all_rows),
        'due_soon_total': sum(int(row.get('due_soon_count') or 0) for row in all_rows),
    }


def build_pending_assignment_manager_rows(period_id: int, *, reminder_interval_hours: int = REMINDER_COOLDOWN_HOURS) -> list[dict[str, Any]]:
    dashboard = build_pending_assignment_manager_dashboard(period_id, reminder_interval_hours=reminder_interval_hours)
    return list(dashboard.get('eligible_rows') or [])




__all__ = [name for name in globals() if not name.startswith("__")]
