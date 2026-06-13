# -*- coding: utf-8 -*-
"""
BYS360 Performans Tamamlama Faz 9
Otomatik Hatırlatma ve Aksatan Amir Bildirimi Politika Merkezi

Amaç:
- Bekleyen değerlendirme görevlerini izlemek.
- Son tarih yaklaşınca amire hatırlatma üretmek.
- Son tarih geçtiyse aksatan amir olarak işaretlemek.
- Aksatan amir raporu ve bildirim/mail log sözleşmesini kurmak.
- Hatırlatmaları sahte görev üretmeden, gerçek bekleyen görevlerden üretmek.
"""
from __future__ import annotations


from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Mapping, Optional
import logging
logger = logging.getLogger(__name__)


PHASE9_POLICY_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE9_REMINDER_POLICY"

TASK_STATUS_PENDING = "pending"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_CANCELLED = "cancelled"

REMINDER_LEVEL_INFO = "info"
REMINDER_LEVEL_WARNING = "warning"
REMINDER_LEVEL_OVERDUE = "overdue"

REMINDER_LABELS = {
    REMINDER_LEVEL_INFO: "Hatırlatma",
    REMINDER_LEVEL_WARNING: "Son Tarih Yaklaşıyor",
    REMINDER_LEVEL_OVERDUE: "Süre Geçti / Aksatan Amir",
}

CHANNEL_LABELS = {
    "notification": "Sistem Bildirimi",
    "email": "E-posta",
    "both": "Sistem Bildirimi ve E-posta",
}


@dataclass(frozen=True)
class ReminderDecision:
    should_notify: bool
    level: str
    label: str
    overdue: bool
    overdue_days: int
    days_left: Optional[int]
    channel: str
    channel_label: str
    message: str


@dataclass(frozen=True)
class ManagerDelaySummary:
    manager_id: Any
    manager_name: str
    pending_count: int
    overdue_count: int
    max_overdue_days: int
    status_label: str


def _parse_date(value: Any) -> Optional[date]:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/phase9_reminder_policy.py")
    return None


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "evet", "on", "aktif", "enabled"}


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/phase9_reminder_policy.py | line=97")
        return default


def normalize_task_status(value: Any) -> str:
    raw = str(value or TASK_STATUS_PENDING).strip().lower()
    if raw in {"done", "completed", "tamamlandi", "tamamlandı"}:
        return TASK_STATUS_COMPLETED
    if raw in {"cancelled", "canceled", "iptal"}:
        return TASK_STATUS_CANCELLED
    return TASK_STATUS_PENDING


def is_pending_task(task: Mapping[str, Any]) -> bool:
    return normalize_task_status(task.get("status") or task.get("task_status") or task.get("state")) == TASK_STATUS_PENDING


def resolve_reminder_decision(
    *,
    due_date: Any,
    today: Optional[date] = None,
    task_status: Any = TASK_STATUS_PENDING,
    settings: Optional[Mapping[str, Any]] = None,
) -> ReminderDecision:
    settings = settings or {}
    today = today or date.today()
    due = _parse_date(due_date)
    status = normalize_task_status(task_status)

    reminder_enabled = _bool(settings.get("performance.phase9.reminders_enabled", True), True)
    overdue_enabled = _bool(settings.get("performance.phase9.overdue_tracking_enabled", True), True)
    threshold_days = _int(settings.get("performance.phase9.due_soon_days", 3), 3)
    channel = str(settings.get("performance.phase9.default_channel", "both") or "both").strip().lower()
    if channel not in CHANNEL_LABELS:
        channel = "both"

    if not reminder_enabled or status != TASK_STATUS_PENDING or not due:
        return ReminderDecision(
            should_notify=False,
            level=REMINDER_LEVEL_INFO,
            label="Hatırlatma Gerekmiyor",
            overdue=False,
            overdue_days=0,
            days_left=None,
            channel=channel,
            channel_label=CHANNEL_LABELS[channel],
            message="Bu görev için otomatik hatırlatma gerekmiyor.",
        )

    delta = (due - today).days

    if delta < 0 and overdue_enabled:
        overdue_days = abs(delta)
        return ReminderDecision(
            should_notify=True,
            level=REMINDER_LEVEL_OVERDUE,
            label=REMINDER_LABELS[REMINDER_LEVEL_OVERDUE],
            overdue=True,
            overdue_days=overdue_days,
            days_left=0,
            channel=channel,
            channel_label=CHANNEL_LABELS[channel],
            message=f"Değerlendirme görevinin son tarihi {overdue_days} gün önce geçti. Görev aksatan amir listesine alınmalıdır.",
        )

    if 0 <= delta <= threshold_days:
        return ReminderDecision(
            should_notify=True,
            level=REMINDER_LEVEL_WARNING,
            label=REMINDER_LABELS[REMINDER_LEVEL_WARNING],
            overdue=False,
            overdue_days=0,
            days_left=delta,
            channel=channel,
            channel_label=CHANNEL_LABELS[channel],
            message=f"Değerlendirme görevinin son tarihine {delta} gün kaldı.",
        )

    return ReminderDecision(
        should_notify=False,
        level=REMINDER_LEVEL_INFO,
        label=REMINDER_LABELS[REMINDER_LEVEL_INFO],
        overdue=False,
        overdue_days=0,
        days_left=delta,
        channel=channel,
        channel_label=CHANNEL_LABELS[channel],
        message="Son tarih henüz yaklaşmadı.",
    )


def build_reminder_payload(task: Mapping[str, Any], *, today: Optional[date] = None, settings: Optional[Mapping[str, Any]] = None) -> Optional[Dict[str, Any]]:
    if not is_pending_task(task):
        return None

    decision = resolve_reminder_decision(
        due_date=task.get("due_date") or task.get("deadline") or task.get("son_tarih"),
        today=today,
        task_status=task.get("status") or task.get("task_status") or task.get("state"),
        settings=settings,
    )

    if not decision.should_notify:
        return None

    manager_name = task.get("manager_name") or task.get("amir_adi") or "Değerlendirici"
    employee_name = task.get("employee_name") or task.get("personel_adi") or "Personel"
    period_title = task.get("period_title") or task.get("donem") or "Performans dönemi"

    return {
        "task_id": task.get("id") or task.get("task_id"),
        "manager_id": task.get("manager_id") or task.get("amir_id"),
        "manager_name": manager_name,
        "employee_id": task.get("employee_id") or task.get("personel_id"),
        "employee_name": employee_name,
        "period_title": period_title,
        "level": decision.level,
        "label": decision.label,
        "overdue": decision.overdue,
        "overdue_days": decision.overdue_days,
        "days_left": decision.days_left,
        "channel": decision.channel,
        "channel_label": decision.channel_label,
        "subject": f"BYS360 Performans Değerlendirme Hatırlatması - {period_title}",
        "message": f"{manager_name}, {employee_name} için bekleyen değerlendirme göreviniz bulunmaktadır. {decision.message}",
    }


def collect_reminder_payloads(tasks: Iterable[Mapping[str, Any]], *, today: Optional[date] = None, settings: Optional[Mapping[str, Any]] = None) -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []
    seen_task_ids = set()

    for task in tasks or []:
        payload = build_reminder_payload(task, today=today, settings=settings)
        if not payload:
            continue
        task_id = payload.get("task_id")
        if task_id and task_id in seen_task_ids:
            continue
        if task_id:
            seen_task_ids.add(task_id)
        payloads.append(payload)

    return payloads


def summarize_delayed_managers(tasks: Iterable[Mapping[str, Any]], *, today: Optional[date] = None) -> List[ManagerDelaySummary]:
    today = today or date.today()
    bucket: Dict[Any, Dict[str, Any]] = {}

    for task in tasks or []:
        if not is_pending_task(task):
            continue

        manager_id = task.get("manager_id") or task.get("amir_id")
        if manager_id is None:
            continue

        due = _parse_date(task.get("due_date") or task.get("deadline") or task.get("son_tarih"))
        overdue_days = 0
        if due and due < today:
            overdue_days = (today - due).days

        row = bucket.setdefault(
            manager_id,
            {
                "manager_id": manager_id,
                "manager_name": task.get("manager_name") or task.get("amir_adi") or "Değerlendirici",
                "pending_count": 0,
                "overdue_count": 0,
                "max_overdue_days": 0,
            },
        )
        row["pending_count"] += 1
        if overdue_days > 0:
            row["overdue_count"] += 1
            row["max_overdue_days"] = max(row["max_overdue_days"], overdue_days)

    result: List[ManagerDelaySummary] = []
    for row in bucket.values():
        status = "Aksatan Amir" if row["overdue_count"] else "Bekleyen Görev Var"
        result.append(
            ManagerDelaySummary(
                manager_id=row["manager_id"],
                manager_name=row["manager_name"],
                pending_count=row["pending_count"],
                overdue_count=row["overdue_count"],
                max_overdue_days=row["max_overdue_days"],
                status_label=status,
            )
        )

    return sorted(result, key=lambda x: (x.overdue_count, x.max_overdue_days, x.pending_count), reverse=True)


def build_notification_log_entry(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Bildirim/mail log için teknik olmayan, izlenebilir kayıt sözleşmesi.
    """
    return {
        "task_id": payload.get("task_id"),
        "manager_id": payload.get("manager_id"),
        "employee_id": payload.get("employee_id"),
        "channel": payload.get("channel", "both"),
        "status": "Hazırlandı",
        "subject": payload.get("subject"),
        "summary": payload.get("message"),
        "level": payload.get("level"),
        "overdue": bool(payload.get("overdue")),
    }


def phase9_reminder_contract() -> Dict[str, Any]:
    return {
        "pending_tasks_tracked": True,
        "due_soon_reminders": True,
        "overdue_manager_detection": True,
        "delayed_manager_report": True,
        "notification_payload": True,
        "email_log_payload": True,
        "duplicate_task_notification_prevented": True,
        "completed_tasks_ignored": True,
        "phase_marker": PHASE9_POLICY_MARKER,
    }

# BYS360_PERFORMANCE_COMPLETION_PHASE9_REMINDER_BOUND
# Otomatik hatırlatma ve aksatan amir bildirimi phase9_reminder_policy sözleşmesini kullanır.
