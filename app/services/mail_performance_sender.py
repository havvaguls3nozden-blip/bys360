from __future__ import annotations



from app.services.mail_core import *  # noqa: F401,F403
from app.services.mail_performance_builder import *  # noqa: F401,F403

def _send_assignment_reminder_to_manager(
    manager: User,
    period: PerformancePeriod,
    pending_count: int,
    *,
    actor_user_id: int | None = None,
    reminder_interval_hours: int = REMINDER_COOLDOWN_HOURS,
    force: bool = False,
) -> dict[str, Any]:
    email = _normalize_email_address(getattr(manager, "email", "") or "")
    if not email:
        return {
            "ok": False,
            "status": "failed",
            "message": "Yönetici e-posta adresi bulunamadı.",
            "manager_id": getattr(manager, "id", None),
            "manager_name": f"{getattr(manager, 'ad', '')} {getattr(manager, 'soyad', '')}".strip(),
            "email": getattr(manager, "email", None),
        }

    last_log = get_last_assignment_reminder(period.id, manager.id, success_only=True)
    if not force and last_log and last_log.sent_at:
        next_allowed_at = last_log.sent_at + timedelta(hours=max(int(reminder_interval_hours or REMINDER_COOLDOWN_HOURS), 1))
        if utc_now() < next_allowed_at:
            return {
                "ok": False,
                "status": "skipped",
                "message": f"Son hatırlatma {last_log.sent_at:%d.%m.%Y %H:%M} tarihinde gönderildi.",
                "manager_id": manager.id,
                "manager_name": f"{manager.ad} {manager.soyad}",
                "email": email,
                "last_reminder_at": last_log.sent_at,
                "next_allowed_at": next_allowed_at,
            }

    subject, body = build_assignment_reminder_email(manager, period, pending_count)
    ok, message = send_email(email, subject, body)
    create_mail_log(
        mail_type=PERFORMANCE_REMINDER_MAIL_TYPE,
        recipient_email=email,
        subject=subject,
        body=body,
        period_id=period.id,
        user_id=manager.id,
        sent_by_id=actor_user_id,
        is_success=ok,
        error_message=None if ok else message,
    )
    return {
        "ok": ok,
        "status": "sent" if ok else "failed",
        "message": message,
        "manager_id": manager.id,
        "manager_name": f"{manager.ad} {manager.soyad}",
        "email": email,
    }


def send_single_assignment_reminder(
    period: PerformancePeriod,
    manager: User,
    *,
    actor_user_id: int | None = None,
    reminder_interval_hours: int = REMINDER_COOLDOWN_HOURS,
    force: bool = False,
) -> dict[str, Any]:
    grouped = get_pending_assignment_managers(period.id)
    selected_item = next((x for x in grouped if x["manager"].id == manager.id), None)
    if not selected_item:
        return {
            "ok": False,
            "status": "missing",
            "message": "Bu yönetici için bekleyen görev bulunamadı.",
            "manager_id": manager.id,
            "manager_name": f"{manager.ad} {manager.soyad}",
            "email": getattr(manager, "email", None),
        }

    return _send_assignment_reminder_to_manager(
        manager,
        period,
        int(selected_item.get("pending_count") or 0),
        actor_user_id=actor_user_id,
        reminder_interval_hours=reminder_interval_hours,
        force=force,
    )


def send_selected_assignment_reminders(
    period: PerformancePeriod,
    manager_ids: list[int] | tuple[int, ...] | set[int],
    *,
    actor_user_id: int | None = None,
    reminder_interval_hours: int = REMINDER_COOLDOWN_HOURS,
    force: bool = False,
) -> dict[str, Any]:
    selected_ids = {int(item) for item in (manager_ids or []) if str(item).strip()}
    managers = [item for item in get_pending_assignment_managers(period.id) if getattr(item.get("manager"), "id", None) in selected_ids]

    success_count = 0
    failed_count = 0
    skipped_count = 0
    failed_items: list[dict[str, Any]] = []
    skipped_items: list[dict[str, Any]] = []

    for item in managers:
        result = _send_assignment_reminder_to_manager(
            item["manager"],
            period,
            int(item.get("pending_count") or 0),
            actor_user_id=actor_user_id,
            reminder_interval_hours=reminder_interval_hours,
            force=force,
        )
        if result["status"] == "sent":
            success_count += 1
        elif result["status"] == "skipped":
            skipped_count += 1
            skipped_items.append(result)
        else:
            failed_count += 1
            failed_items.append(result)

    return {
        "total_managers": len(managers),
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "failed_items": failed_items,
        "skipped_items": skipped_items,
    }


def send_bulk_assignment_reminders(
    period: PerformancePeriod,
    *,
    actor_user_id: int | None = None,
    reminder_interval_hours: int = REMINDER_COOLDOWN_HOURS,
    force: bool = False,
) -> dict[str, Any]:
    managers = get_pending_assignment_managers(period.id)

    success_count = 0
    failed_count = 0
    skipped_count = 0
    failed_items: list[dict[str, Any]] = []
    skipped_items: list[dict[str, Any]] = []

    for item in managers:
        manager = item["manager"]
        pending_count = int(item.get("pending_count") or 0)
        result = _send_assignment_reminder_to_manager(
            manager,
            period,
            pending_count,
            actor_user_id=actor_user_id,
            reminder_interval_hours=reminder_interval_hours,
            force=force,
        )
        if result["status"] == "sent":
            success_count += 1
        elif result["status"] == "skipped":
            skipped_count += 1
            skipped_items.append(result)
        else:
            failed_count += 1
            failed_items.append(result)

    return {
        "total_managers": len(managers),
        "success_count": success_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "failed_items": failed_items,
        "skipped_items": skipped_items,
    }


def _build_score_line(score_value: Any) -> str:
    try:
        value = float(score_value or 0)
        return f"{value:.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return "0"


def _build_results_published_email(recipient_name: str, evaluation: PerformanceEvaluation) -> tuple[str, str]:
    template = get_mail_template_content(PERFORMANCE_RESULT_MAIL_TYPE)
    period = evaluation.period
    employee = evaluation.employee
    publish_time = getattr(evaluation, "published_to_employee_at", None) or getattr(period, "published_at", None)
    context = {
        **_build_mail_common_context(),
        "recipient_name": recipient_name,
        "period_title": getattr(period, "title", "-") or "-",
        "employee_name": f"{getattr(employee, 'ad', '')} {getattr(employee, 'soyad', '')}".strip() or "-",
        "sicil_no": getattr(employee, "sicil_no", "-") or "-",
        "final_score": _build_score_line(getattr(evaluation, "final_total_100", 0)),
        "publish_date": publish_time.strftime("%d.%m.%Y %H:%M") if publish_time else "-",
    }
    subject = _render_text_template(template["subject"], context)
    body = _render_text_template(template["body"], context)
    return subject, body


def _collect_publish_recipients(evaluation: PerformanceEvaluation) -> list[tuple[str, str, int | None]]:
    recipients: list[tuple[str, str, int | None]] = []
    seen: set[str] = set()

    def add_user(user: User | None) -> None:
        email = _normalize_email_address(getattr(user, "email", "") or "") if user else ""
        if not user or not email or email in seen:
            return
        seen.add(email)
        recipients.append((email, f"{user.ad} {user.soyad}", getattr(user, "id", None)))

    add_user(getattr(evaluation, "employee", None))
    add_user(getattr(evaluation, "level_1_evaluator", None))
    add_user(getattr(evaluation, "level_2_evaluator", None))
    add_user(getattr(evaluation, "level_3_evaluator", None))
    return recipients


def send_published_evaluation_notifications(
    period: PerformancePeriod,
    evaluation_ids: list[int] | tuple[int, ...] | set[int] | None,
    *,
    actor_user_id: int | None = None,
) -> dict[str, Any]:
    ids = [int(item) for item in (evaluation_ids or []) if item is not None]
    if not period or not ids:
        return {
            "evaluation_count": 0,
            "recipient_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "failed_items": [],
        }

    evaluations = PerformanceEvaluation.query.filter(PerformanceEvaluation.id.in_(ids)).all()

    success_count = 0
    failed_count = 0
    recipient_count = 0
    failed_items: list[dict[str, Any]] = []

    for evaluation in evaluations:
        for email, display_name, user_id in _collect_publish_recipients(evaluation):
            subject, body = _build_results_published_email(display_name, evaluation)
            ok, message = send_email(email, subject, body)
            create_mail_log(
                mail_type=PERFORMANCE_RESULT_MAIL_TYPE,
                recipient_email=email,
                subject=subject,
                body=body,
                period_id=period.id,
                user_id=user_id,
                sent_by_id=actor_user_id,
                is_success=ok,
                error_message=None if ok else message,
            )
            recipient_count += 1
            if ok:
                success_count += 1
            else:
                failed_count += 1
                failed_items.append(
                    {
                        "evaluation_id": evaluation.id,
                        "employee_id": evaluation.employee_id,
                        "email": email,
                        "name": display_name,
                        "error": message,
                    }
                )

    return {
        "evaluation_count": len(evaluations),
        "recipient_count": recipient_count,
        "success_count": success_count,
        "failed_count": failed_count,
        "failed_items": failed_items,
    }


def get_failed_performance_mail_logs(
    *,
    period_id: int | None = None,
    mail_types: list[str] | tuple[str, ...] | set[str] | None = None,
    limit: int = 50,
) -> list[MailLog]:
    types = tuple(mail_types or (PERFORMANCE_REMINDER_MAIL_TYPE, PERFORMANCE_RESULT_MAIL_TYPE))
    query = MailLog.query.filter(MailLog.is_success.is_(False), MailLog.mail_type.in_(types))
    if period_id:
        query = query.filter(MailLog.related_period_id == period_id)
    return query.order_by(MailLog.sent_at.desc(), MailLog.id.desc()).limit(max(int(limit or 50), 1)).all()


def retry_mail_log(mail_log_or_id: MailLog | int, *, actor_user_id: int | None = None) -> dict[str, Any]:
    mail_log = mail_log_or_id if isinstance(mail_log_or_id, MailLog) else db.session.get(MailLog, int(mail_log_or_id))
    if not mail_log:
        return {"ok": False, "status": "missing", "message": "Mail log kaydı bulunamadı."}

    subject = _clean_header_value(getattr(mail_log, "subject", "") or "")
    body = (getattr(mail_log, "body_preview", "") or "").strip()
    email = _normalize_email_address(getattr(mail_log, "recipient_email", "") or "")
    if not email or not subject or not body:
        return {
            "ok": False,
            "status": "invalid",
            "message": "Yeniden gönderim için gerekli mail içeriği eksik.",
            "mail_log_id": mail_log.id,
        }

    ok, message = send_email(email, subject, body)
    retry_log = create_mail_log(
        mail_type=mail_log.mail_type,
        recipient_email=email,
        subject=subject,
        body=body,
        period_id=getattr(mail_log, "related_period_id", None),
        user_id=getattr(mail_log, "related_user_id", None),
        feedback_request_id=getattr(mail_log, "related_feedback_request_id", None),
        sent_by_id=actor_user_id,
        is_success=ok,
        error_message=None if ok else message,
    )
    return {
        "ok": ok,
        "status": "sent" if ok else "failed",
        "message": message,
        "mail_log_id": mail_log.id,
        "retry_log_id": getattr(retry_log, "id", None),
        "recipient_email": email,
        "mail_type": mail_log.mail_type,
    }


def retry_failed_performance_mail_logs(
    *,
    period_id: int | None = None,
    mail_types: list[str] | tuple[str, ...] | set[str] | None = None,
    actor_user_id: int | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    logs = get_failed_performance_mail_logs(period_id=period_id, mail_types=mail_types, limit=limit)
    success_count = 0
    failed_count = 0
    items: list[dict[str, Any]] = []
    for row in logs:
        result = retry_mail_log(row, actor_user_id=actor_user_id)
        items.append(result)
        if result.get("ok"):
            success_count += 1
        else:
            failed_count += 1
    return {
        "total_logs": len(logs),
        "success_count": success_count,
        "failed_count": failed_count,
        "items": items,
    }



def get_performance_mail_automation_settings() -> dict[str, Any]:
    def _get_value(setting_key: str) -> str:
        definition = AUTOMATION_SETTING_DEFINITIONS[setting_key]
        return _get_mail_template_setting_value(setting_key, definition["default"])

    run_hour = _coerce_int_text(_get_value(PERFORMANCE_MAIL_AUTOMATION_RUN_HOUR_KEY), 9, minimum=0, maximum=23)
    interval_hours = _coerce_int_text(_get_value(PERFORMANCE_MAIL_AUTOMATION_INTERVAL_KEY), REMINDER_COOLDOWN_HOURS, minimum=1, maximum=168)
    min_pending_count = _coerce_int_text(_get_value(PERFORMANCE_MAIL_AUTOMATION_MIN_PENDING_KEY), 1, minimum=1, maximum=999)
    max_periods = _coerce_int_text(_get_value(PERFORMANCE_MAIL_AUTOMATION_MAX_PERIODS_KEY), 3, minimum=1, maximum=25)
    enabled = _coerce_bool_text(_get_value(PERFORMANCE_MAIL_AUTOMATION_ENABLED_KEY), False)
    force_send = _coerce_bool_text(_get_value(PERFORMANCE_MAIL_AUTOMATION_FORCE_SEND_KEY), False)
    only_active_periods = _coerce_bool_text(_get_value(PERFORMANCE_MAIL_AUTOMATION_ONLY_ACTIVE_KEY), True)
    only_during_window = _coerce_bool_text(_get_value(PERFORMANCE_MAIL_AUTOMATION_ONLY_WINDOW_KEY), True)

    run_label = f"Her gün {run_hour:02d}:00"
    command = f"python scripts/performance_mail_automation_runner.py --hour {run_hour}"
    return {
        "enabled": enabled,
        "run_hour": run_hour,
        "run_label": run_label,
        "min_pending_count": min_pending_count,
        "max_periods": max_periods,
        "force_send": force_send,
        "only_active_periods": only_active_periods,
        "only_during_window": only_during_window,
        "reminder_interval_hours": interval_hours,
        "command": command,
    }


def save_performance_mail_automation_settings(payload: dict[str, Any], *, actor_user_id: int | None = None) -> int:
    if not _system_settings_ready():
        raise RuntimeError("system_settings tablosu bulunamadı. Önce flask db upgrade çalıştırın.")

    normalized = {
        PERFORMANCE_MAIL_AUTOMATION_ENABLED_KEY: "1" if _coerce_bool_text(payload.get("enabled"), False) else "0",
        PERFORMANCE_MAIL_AUTOMATION_RUN_HOUR_KEY: str(_coerce_int_text(payload.get("run_hour"), 9, minimum=0, maximum=23)),
        PERFORMANCE_MAIL_AUTOMATION_MIN_PENDING_KEY: str(_coerce_int_text(payload.get("min_pending_count"), 1, minimum=1, maximum=999)),
        PERFORMANCE_MAIL_AUTOMATION_MAX_PERIODS_KEY: str(_coerce_int_text(payload.get("max_periods"), 3, minimum=1, maximum=25)),
        PERFORMANCE_MAIL_AUTOMATION_FORCE_SEND_KEY: "1" if _coerce_bool_text(payload.get("force_send"), False) else "0",
        PERFORMANCE_MAIL_AUTOMATION_ONLY_ACTIVE_KEY: "1" if _coerce_bool_text(payload.get("only_active_periods"), True) else "0",
        PERFORMANCE_MAIL_AUTOMATION_ONLY_WINDOW_KEY: "1" if _coerce_bool_text(payload.get("only_during_window"), True) else "0",
        PERFORMANCE_MAIL_AUTOMATION_INTERVAL_KEY: str(_coerce_int_text(payload.get("reminder_interval_hours"), REMINDER_COOLDOWN_HOURS, minimum=1, maximum=168)),
    }

    changed = 0
    for setting_key, definition in AUTOMATION_SETTING_DEFINITIONS.items():
        value_text = normalized[setting_key]
        current_value = _get_mail_template_setting_value(setting_key, definition["default"])
        if str(current_value).strip() != value_text:
            changed += 1
        _upsert_template_setting(
            setting_key=setting_key,
            label=definition["label"],
            value_text=value_text,
            description=definition["description"],
            updated_by_user_id=actor_user_id,
        )
    return changed


def build_mail_system_health_snapshot(*, period_id: int | None = None) -> dict[str, Any]:
    settings = get_smtp_settings()
    issues: list[str] = []
    if not settings.get('host'):
        issues.append('MAIL_SERVER tanımlı değil.')
    if not settings.get('default_sender'):
        issues.append('MAIL_DEFAULT_SENDER tanımlı değil.')
    if settings.get('use_tls') and int(settings.get('port') or 0) not in {25, 465, 587}:
        issues.append('TLS açık ancak port değeri alışılmış SMTP portlarından farklı görünüyor.')
    if settings.get('username') and not settings.get('password'):
        issues.append('MAIL_USERNAME tanımlı ama MAIL_PASSWORD boş.')

    recent_failed = get_failed_performance_mail_logs(period_id=period_id, limit=5)
    return {
        'ready': len(issues) == 0,
        'host': settings.get('host') or '-',
        'port': settings.get('port') or '-',
        'use_tls': bool(settings.get('use_tls')),
        'default_sender': settings.get('default_sender') or '-',
        'username_masked': _mask_email_address(settings.get('username') or ''),
        'issues': issues,
        'issue_count': len(issues),
        'recent_failed_count': len(recent_failed),
        'recent_failed_preview': (getattr(recent_failed[0], 'error_message', None) if recent_failed else None) or '-',
    }


def send_test_performance_mail(to_email: str, *, actor_user_id: int | None = None) -> dict[str, Any]:
    target = _normalize_email_address(to_email or '')
    if not target:
        return {'ok': False, 'message': 'Geçerli bir test e-posta adresi giriniz.'}

    settings = get_smtp_settings()
    subject = f"BYS360 SMTP test maili | {utc_now().strftime('%d.%m.%Y %H:%M')}"
    body = (
        'Bu mesaj BYS360 performans mail hatırlatma merkezi üzerinden gönderilen test e-postasıdır.\n\n'
        f"SMTP sunucusu: {settings.get('host') or '-'}:{settings.get('port') or '-'}\n"
        f"TLS: {'Açık' if settings.get('use_tls') else 'Kapalı'}\n"
        f"Gönderen: {settings.get('default_sender') or '-'}\n"
        f"Uygulama: {settings.get('app_name') or 'BYS360'}\n"
        f"Kurum: {settings.get('institution_name') or '-'}\n\n"
        'Bu mesajın ulaşması, temel SMTP ayarlarının çalıştığını gösterir.'
    )
    ok, message = send_email(target, subject, body)
    create_mail_log(
        mail_type=PERFORMANCE_TEST_MAIL_TYPE,
        recipient_email=target,
        subject=subject,
        body=body,
        sent_by_id=actor_user_id,
        is_success=ok,
        error_message=None if ok else message,
    )
    return {'ok': ok, 'message': message, 'recipient_email': target, 'subject': subject}

def get_recent_performance_mail_logs(*, period_id: int | None = None, limit: int = 120) -> list[MailLog]:
    query = MailLog.query.filter(MailLog.mail_type.in_((PERFORMANCE_REMINDER_MAIL_TYPE, PERFORMANCE_RESULT_MAIL_TYPE)))
    if period_id:
        query = query.filter(MailLog.related_period_id == period_id)
    return query.order_by(MailLog.sent_at.desc(), MailLog.id.desc()).limit(max(int(limit or 120), 1)).all()


def build_performance_mail_history_rows(*, period_id: int | None = None, limit: int = 120) -> list[dict[str, Any]]:
    rows = []
    for log in get_recent_performance_mail_logs(period_id=period_id, limit=limit):
        rows.append({
            "id": log.id,
            "mail_type": log.mail_type,
            "recipient_email": log.recipient_email,
            "user_name": f"{getattr(log.user, 'ad', '')} {getattr(log.user, 'soyad', '')}".strip() if getattr(log, 'user', None) else "",
            "subject": log.subject,
            "sent_at": log.sent_at,
            "is_success": bool(log.is_success),
            "error_message": log.error_message,
            "sent_by_name": f"{getattr(log.sent_by, 'ad', '')} {getattr(log.sent_by, 'soyad', '')}".strip() if getattr(log, 'sent_by', None) else "",
        })
    return rows


def build_reminder_activity_dashboard(period_id: int, *, limit: int = 12) -> dict[str, Any]:
    logs = (
        MailLog.query
        .filter(
            MailLog.mail_type == PERFORMANCE_REMINDER_MAIL_TYPE,
            MailLog.related_period_id == period_id,
        )
        .order_by(MailLog.sent_at.desc(), MailLog.id.desc())
        .all()
    )

    grouped: dict[str, dict[str, Any]] = {}
    for log in logs:
        key = str(getattr(log, 'related_user_id', None) or getattr(log, 'recipient_email', '') or f"anon:{log.id}")
        bucket = grouped.setdefault(
            key,
            {
                "manager_id": getattr(log, 'related_user_id', None),
                "manager_name": f"{getattr(log.user, 'ad', '')} {getattr(log.user, 'soyad', '')}".strip() if getattr(log, 'user', None) else (getattr(log, 'recipient_email', '') or '-'),
                "recipient_email": getattr(log, 'recipient_email', ''),
                "sent_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "last_sent_at": None,
            },
        )
        bucket["sent_count"] += 1
        if log.is_success:
            bucket["success_count"] += 1
        else:
            bucket["failed_count"] += 1
        if not bucket["last_sent_at"] or (log.sent_at and log.sent_at > bucket["last_sent_at"]):
            bucket["last_sent_at"] = log.sent_at

    rows = sorted(grouped.values(), key=lambda row: (-row["sent_count"], (row["manager_name"] or '').lower()))[: max(int(limit or 12), 1)]
    return {
        "total_sent": len(logs),
        "unique_manager_count": len(grouped),
        "success_count": sum(1 for log in logs if log.is_success),
        "failed_count": sum(1 for log in logs if not log.is_success),
        "top_rows": rows,
    }


def _bucket_mail_error_message(message: str | None) -> str:
    text = (message or "").strip().lower()
    if not text:
        return "Bilinmeyen hata"
    if any(token in text for token in ["auth", "login", "username", "password", "authentication"]):
        return "Kimlik doğrulama"
    if any(token in text for token in ["timeout", "timed out"]):
        return "Zaman aşımı"
    if any(token in text for token in ["refused", "connect", "connection", "network", "unreachable"]):
        return "Bağlantı"
    if any(token in text for token in ["recipient", "address", "mailbox", "invalid", "user unknown"]):
        return "Alıcı adresi"
    if any(token in text for token in ["tls", "ssl", "certificate"]):
        return "TLS / sertifika"
    if any(token in text for token in ["server", "smtp"]):
        return "Sunucu yanıtı"
    return "Diğer"


def build_failed_mail_dashboard(*, period_id: int | None = None, limit: int = 100) -> dict[str, Any]:
    logs = get_failed_performance_mail_logs(period_id=period_id, limit=limit)
    counter = Counter(_bucket_mail_error_message(getattr(log, 'error_message', None)) for log in logs)
    rows = [{"label": label, "count": count} for label, count in counter.most_common()]
    return {
        "total_failed": len(logs),
        "error_buckets": rows,
        "latest_error": getattr(logs[0], 'error_message', None) if logs else None,
    }


def _iter_automation_periods(*, period_id: int | None = None, now: datetime | None = None, settings: dict[str, Any] | None = None) -> list[PerformancePeriod]:
    if period_id:
        period = db.session.get(PerformancePeriod, int(period_id))
        return [period] if period else []

    now = now or utc_now()
    today = now.date()
    settings = settings or get_performance_mail_automation_settings()
    query = PerformancePeriod.query.order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
    if settings.get("only_active_periods", True):
        query = query.filter(PerformancePeriod.is_active.is_(True))
    periods = query.limit(max(int(settings.get("max_periods") or 3), 1) * 3).all()
    selected: list[PerformancePeriod] = []
    for period in periods:
        if settings.get("only_during_window", True) and not period.is_evaluation_open_on(today):
            continue
        selected.append(period)
        if len(selected) >= max(int(settings.get("max_periods") or 3), 1):
            break
    return selected


def run_performance_mail_automation(
    *,
    actor_user_id: int | None = None,
    period_id: int | None = None,
    force: bool | None = None,
    dry_run: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    settings = get_performance_mail_automation_settings()
    now = now or utc_now()
    if force is None:
        force = bool(settings.get("force_send"))

    periods = _iter_automation_periods(period_id=period_id, now=now, settings=settings)
    period_items: list[dict[str, Any]] = []
    total_success = 0
    total_failed = 0
    total_skipped = 0
    total_managers = 0
    total_pending = 0

    for period in periods:
        manager_rows = [
            row
            for row in build_pending_assignment_manager_rows(period.id, reminder_interval_hours=int(settings.get("reminder_interval_hours") or REMINDER_COOLDOWN_HOURS))
            if int(row.get("count") or 0) >= int(settings.get("min_pending_count") or 1)
        ]
        total_pending += sum(int(row.get("count") or 0) for row in manager_rows)
        total_managers += len(manager_rows)
        if dry_run:
            period_items.append({
                "period_id": period.id,
                "period_title": period.title,
                "manager_count": len(manager_rows),
                "pending_count": sum(int(row.get("count") or 0) for row in manager_rows),
                "dry_run": True,
            })
            continue

        manager_ids = [int(row["manager"].id) for row in manager_rows]
        result = send_selected_assignment_reminders(
            period,
            manager_ids,
            actor_user_id=actor_user_id,
            reminder_interval_hours=int(settings.get("reminder_interval_hours") or REMINDER_COOLDOWN_HOURS),
            force=bool(force),
        ) if manager_ids else {"total_managers": 0, "success_count": 0, "failed_count": 0, "skipped_count": 0}

        total_success += int(result.get("success_count") or 0)
        total_failed += int(result.get("failed_count") or 0)
        total_skipped += int(result.get("skipped_count") or 0)
        period_items.append({
            "period_id": period.id,
            "period_title": period.title,
            "manager_count": len(manager_ids),
            "pending_count": sum(int(row.get("count") or 0) for row in manager_rows),
            **result,
        })

    return {
        "ran_at": now,
        "settings": settings,
        "dry_run": bool(dry_run),
        "period_count": len(periods),
        "period_items": period_items,
        "total_managers": total_managers,
        "total_pending": total_pending,
        "success_count": total_success,
        "failed_count": total_failed,
        "skipped_count": total_skipped,
        "command": settings.get("command"),
    }




__all__ = [name for name in globals() if not name.startswith("__")]
