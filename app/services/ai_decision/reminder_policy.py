from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

"""BYS360 AI Karar Destek Faz 9 hatırlatma ve aksatan amir politikası.

Değerlendirme görevlerinin son tarih, bekleme ve gecikme durumlarını insan
kontrollü karar destek sinyallerine dönüştürür. Çıktı idari karar üretmez;
yalnızca süreç takibi için özet, uyarı ve öneri sunar.

BYS360_AI_DECISION_FAZ9_REMINDER_POLICY
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ReminderPolicy:
    """Otomatik hatırlatma ve aksatan amir karar destek ayarları."""

    enabled: bool = True
    reminder_before_days: int = 3
    overdue_after_days: int = 1
    critical_overdue_days: int = 7
    max_detail_rows: int = 250
    send_email_if_enabled: bool = False
    create_notification_if_enabled: bool = True


_FALSE_VALUES = {"0", "false", "hayır", "hayir", "no", "off", "kapalı", "kapali"}
_TRUE_VALUES = {"1", "true", "evet", "yes", "on", "açık", "acik"}
_COMPLETED_STATUS = {"completed", "done", "submitted", "approved", "published", "tamamlandi", "tamamlandı", "onaylandi", "onaylandı"}
_PENDING_STATUS = {"pending", "waiting", "assigned", "open", "bekliyor", "atanmış", "atanmis", "açık", "acik"}


def safe_attr(source: Any, *names: str, default: Any = None) -> Any:
    """Mapping, SQLAlchemy row veya nesne üzerinden güvenli alan okur."""

    if source is None:
        return default
    mapping = dict(source._mapping) if hasattr(source, "_mapping") else source if isinstance(source, Mapping) else None
    if isinstance(mapping, Mapping):
        for name in names:
            if name in mapping:
                return mapping.get(name)
    for name in names:
        if hasattr(source, name):
            return getattr(source, name)
    return default


def to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text in _FALSE_VALUES:
        return False
    return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(str(value).replace(",", ".")))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/ai_decision/reminder_policy.py | line=72")
        return default


def to_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:19] if "%H" in fmt else text[:10], fmt).date()
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/ai_decision/reminder_policy.py:85)")
            continue
    return None


def today() -> date:
    return date.today()


def build_reminder_policy(settings: Mapping[str, Any] | None = None) -> ReminderPolicy:
    settings = settings or {}
    return ReminderPolicy(
        enabled=to_bool(settings.get("faz9_reminders_enabled"), True),
        reminder_before_days=to_int(settings.get("faz9_reminder_before_days"), 3),
        overdue_after_days=to_int(settings.get("faz9_overdue_after_days"), 1),
        critical_overdue_days=to_int(settings.get("faz9_critical_overdue_days"), 7),
        max_detail_rows=to_int(settings.get("faz9_max_detail_rows"), 250),
        send_email_if_enabled=to_bool(settings.get("faz9_send_email_if_enabled"), False),
        create_notification_if_enabled=to_bool(settings.get("faz9_create_notification_if_enabled"), True),
    )


def normalize_status(value: Any) -> str:
    return str(value or "pending").strip().lower()


def is_completed_assignment(row: Any) -> bool:
    status = normalize_status(safe_attr(row, "status", "assignment_status", "state", default="pending"))
    return status in _COMPLETED_STATUS


def assignment_due_date(row: Any) -> date | None:
    return to_date(safe_attr(row, "due_date", "deadline", "evaluation_deadline", "end_date", "period_end_date", default=None))


def days_until(row: Any, reference_date: date | None = None) -> int | None:
    due = assignment_due_date(row)
    if due is None:
        return None
    reference_date = reference_date or today()
    return (due - reference_date).days


def is_overdue(row: Any, policy: ReminderPolicy | None = None, reference_date: date | None = None) -> bool:
    if is_completed_assignment(row):
        return False
    remaining = days_until(row, reference_date)
    policy = policy or ReminderPolicy()
    return remaining is not None and remaining < -max(policy.overdue_after_days - 1, 0)


def is_due_soon(row: Any, policy: ReminderPolicy | None = None, reference_date: date | None = None) -> bool:
    if is_completed_assignment(row):
        return False
    remaining = days_until(row, reference_date)
    policy = policy or ReminderPolicy()
    return remaining is not None and 0 <= remaining <= policy.reminder_before_days


def is_missing_due_date(row: Any) -> bool:
    return assignment_due_date(row) is None and not is_completed_assignment(row)


def classify_assignment_status(row: Any, policy: ReminderPolicy | None = None, reference_date: date | None = None) -> dict[str, Any]:
    """Tek değerlendirme görevi için kurumsal durum etiketi üretir."""

    policy = policy or ReminderPolicy()
    reference_date = reference_date or today()
    due = assignment_due_date(row)
    remaining = days_until(row, reference_date)
    completed = is_completed_assignment(row)

    if completed:
        label = "Tamamlandı"
        level = "Düzenli"
        attention = []
    elif due is None:
        label = "Son Tarih Bilgisi Eksik"
        level = "Kontrol Gerektirir"
        attention = ["Değerlendirme görevi için son tarih bilgisi görünmüyor."]
    elif remaining is not None and remaining < -policy.critical_overdue_days:
        label = "Kritik Gecikmiş Değerlendirme"
        level = "Kritik"
        attention = ["Değerlendirme son tarihi önemli ölçüde geçmiş görünüyor."]
    elif is_overdue(row, policy, reference_date):
        label = "Gecikmiş Değerlendirme"
        level = "Dikkat Gerektirir"
        attention = ["Değerlendirme son tarihi geçmiş görünüyor."]
    elif is_due_soon(row, policy, reference_date):
        label = "Son Tarihi Yaklaşan Değerlendirme"
        level = "Yakın Takip"
        attention = ["Değerlendirme son tarihi yaklaşıyor."]
    else:
        label = "Süreç Takibinde"
        level = "Düzenli"
        attention = []

    return {
        "assignment_id": safe_attr(row, "id", "assignment_id", default=None),
        "period_id": safe_attr(row, "period_id", "performance_period_id", default=None),
        "evaluator_id": safe_attr(row, "evaluator_id", "manager_id", "supervisor_id", default=None),
        "status_label": label,
        "risk_level": level,
        "due_date": due.isoformat() if due else None,
        "days_until_due": remaining,
        "attention_items": attention,
        "completed": completed,
        "marker": "BYS360_AI_DECISION_FAZ9_ASSIGNMENT_STATUS",
    }


def summarize_assignments(assignments: Iterable[Any], policy: ReminderPolicy | None = None, reference_date: date | None = None) -> dict[str, Any]:
    policy = policy or ReminderPolicy()
    reference_date = reference_date or today()
    rows = list(assignments)
    classified = [classify_assignment_status(row, policy, reference_date) for row in rows]
    pending_count = sum(1 for item in classified if not item["completed"])
    completed_count = sum(1 for item in classified if item["completed"])
    overdue_count = sum(1 for item in classified if item["status_label"] in {"Gecikmiş Değerlendirme", "Kritik Gecikmiş Değerlendirme"})
    critical_count = sum(1 for item in classified if item["risk_level"] == "Kritik")
    due_soon_count = sum(1 for item in classified if item["status_label"] == "Son Tarihi Yaklaşan Değerlendirme")
    missing_due_count = sum(1 for item in classified if item["status_label"] == "Son Tarih Bilgisi Eksik")

    if critical_count:
        manager_note = "Kritik gecikmiş değerlendirmeler öncelikli olarak izlenmelidir."
    elif overdue_count:
        manager_note = "Gecikmiş değerlendirmeler için amir hatırlatma süreci çalıştırılmalıdır."
    elif due_soon_count:
        manager_note = "Son tarihi yaklaşan değerlendirmeler için hatırlatma yapılması uygundur."
    elif missing_due_count:
        manager_note = "Son tarih bilgisi eksik görevler dönem takvimiyle eşleştirilmelidir."
    else:
        manager_note = "Değerlendirme görev takibi karar destek açısından düzenli görünüyor."

    return {
        "assignment_count": len(rows),
        "completed_count": completed_count,
        "pending_count": pending_count,
        "due_soon_count": due_soon_count,
        "overdue_count": overdue_count,
        "critical_overdue_count": critical_count,
        "missing_due_date_count": missing_due_count,
        "policy_enabled": policy.enabled,
        "manager_note": manager_note,
        "marker": "BYS360_AI_DECISION_FAZ9_ASSIGNMENT_SUMMARY",
    }
