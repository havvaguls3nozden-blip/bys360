"""BYS360 Performans Tamamlama Faz 10: Otomatik hatırlatma, aksatan amir ve süreç bildirimleri merkezi.

Bu merkez, performans değerlendirme dönemlerinde bekleyen görevleri, son tarih
hatırlatmalarını, geciken/aksatan amirleri, süreç bildirimlerini ve mail/log
kayıtlarını güvenli biçimde yönetmek için ortak karar katmanı sağlar.

Kritik sınırlar:
- Hatırlatma ve bildirimler otomatik puan, idari karar veya yaptırım üretmez.
- Hafta sonu gönderim kuralı merkezi ayardan okunur.
- Kullanıcı ekranına teknik hata, endpoint, workflow/debug dili taşınmaz.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)

BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_CENTER = True
BYS360_PERFORMANCE_COMPLETION_PHASE10_VERSION = "performance-completion-phase10-reminder-notification-center-v1a"
BYS360_PERFORMANCE_COMPLETION_PHASE10_WEEKDAY_ONLY = True
BYS360_PERFORMANCE_COMPLETION_PHASE10_DELAYED_EVALUATOR_REPORT = True
BYS360_PERFORMANCE_COMPLETION_PHASE10_MAIL_LOG_REQUIRED = True
BYS360_PERFORMANCE_COMPLETION_PHASE10_NO_ADMIN_DECISION = True
BYS360_PERFORMANCE_COMPLETION_PHASE10_TECHNICAL_LANGUAGE_CLEAN = True
BYS360_PERFORMANCE_COMPLETION_PHASE10_PROCESS_VISIBILITY = True

PHASE10_TABLE_NAME = "performance_process_reminder_logs"

REMINDER_TYPE_LABELS = {
    "assignment_created": "Değerlendirme Görevi Oluşturuldu",
    "due_soon": "Son Tarih Yaklaşıyor",
    "due_today": "Bugün Tamamlanması Gerekiyor",
    "overdue": "Geciken Değerlendirme Görevi",
    "manager_delay": "Aksatan Amir Bildirimi",
    "low_score_approval": "Düşük Performans Onay Hatırlatması",
    "publish_preapproval": "Yayın Ön Onayı Hatırlatması",
    "final_publish": "Final Yayın Hatırlatması",
    "process_info": "Süreç Bilgilendirmesi",
}

CHANNEL_LABELS = {
    "mail": "E-posta",
    "notification": "Sistem Bildirimi",
    "dashboard": "Dashboard Uyarısı",
    "log_only": "Sadece Kayıt",
}

STATUS_LABELS = {
    "planned": "Planlandı",
    "skipped_weekend": "Hafta Sonu Kuralı Nedeniyle Gönderilmedi",
    "ready": "Gönderime Hazır",
    "sent": "Gönderildi",
    "failed": "Gönderim Başarısız",
    "cancelled": "İptal Edildi",
    "logged": "Kayıt Altına Alındı",
    "overdue": "Gecikmiş Süreç",
}

DUE_STATUS_LABELS = {
    "not_due": "Süreç Takipte",
    "due_soon": "Son Tarih Yaklaşıyor",
    "due_today": "Bugün Tamamlanmalı",
    "overdue": "Gecikmiş Görev",
    "completed": "Tamamlandı",
}

PHASE10_SETTING_ROWS = [
    ("performance_phase10", "reminder_center_enabled", "Otomatik hatırlatma merkezi aktif", "bool", "true", "Bekleyen performans görevleri için merkezi hatırlatma kararını çalıştırır."),
    ("performance_phase10", "weekday_only_reminders", "Hafta sonu hatırlatma gönderilmesin", "bool", "true", "Cumartesi/Pazar günleri otomatik performans hatırlatmaları gönderilmez."),
    ("performance_phase10", "due_soon_days", "Son tarih yaklaşma gün sayısı", "int", "3", "Son tarihe kaç gün kala hatırlatma üretileceğini belirler."),
    ("performance_phase10", "delayed_evaluator_report_enabled", "Aksatan amir raporu aktif", "bool", "true", "Geciken değerlendirme görevleri amir bazlı raporlanır."),
    ("performance_phase10", "mail_log_required", "Hatırlatma mail log kaydı zorunlu", "bool", "true", "Gönderilen veya atlanan hatırlatmalar kayıt altına alınır."),
    ("performance_phase10", "low_score_approval_reminders", "Düşük performans onay hatırlatması aktif", "bool", "true", "70 altı sonuçlarda onay bekleyen kayıtlar için hatırlatma üretir."),
    ("performance_phase10", "publish_preapproval_reminders", "Yayın ön onay hatırlatması aktif", "bool", "true", "Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayı için hatırlatma üretir."),
    ("performance_phase10", "technical_language_clean", "Bildirimlerde teknik dil temizliği aktif", "bool", "true", "Workflow/debug/endpoint gibi teknik ifadeler kullanıcıya gösterilmez."),
]

TECHNICAL_WORDS = ["workflow", "endpoint", "debug", "traceback", "exception", "authorized_scope", "raw json", "json", "stacktrace", "phase sync"]

@dataclass(frozen=True)
class Phase10ReminderValidation:
    ok: bool
    errors: list[str]
    warnings: list[str]
    normalized: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": list(self.errors), "warnings": list(self.warnings), "normalized": dict(self.normalized)}

@dataclass(frozen=True)
class Phase10ReminderDecision:
    should_send: bool
    status: str
    status_label: str
    reason: str
    channel: str
    weekday_only: bool
    requires_log: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "should_send": self.should_send,
            "status": self.status,
            "status_label": self.status_label,
            "reason": self.reason,
            "channel": self.channel,
            "weekday_only": self.weekday_only,
            "requires_log": self.requires_log,
        }

@dataclass(frozen=True)
class Phase10DelayedEvaluatorSummary:
    evaluator_id: int | None
    evaluator_name: str
    pending_count: int
    overdue_count: int
    due_today_count: int
    due_soon_count: int
    status_label: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "evaluator_id": self.evaluator_id,
            "evaluator_name": self.evaluator_name,
            "pending_count": self.pending_count,
            "overdue_count": self.overdue_count,
            "due_today_count": self.due_today_count,
            "due_soon_count": self.due_soon_count,
            "status_label": self.status_label,
        }


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = _as_text(value).lower()
    if text in {"1", "true", "yes", "evet", "aktif", "on"}:
        return True
    if text in {"0", "false", "no", "hayır", "hayir", "pasif", "off"}:
        return False
    return default


def _as_int(value: Any, default: int | None = None) -> int | None:
    text = _as_text(value)
    if not text:
        return default
    try:
        return int(float(text.replace(",", ".")))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/phase10_reminder_notification_center.py | line=159")
        return default


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _as_text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/performance/phase10_reminder_notification_center.py | line=176")
            continue
    return None


def _as_date_text(value: Any) -> str:
    parsed = _as_date(value)
    if parsed:
        return parsed.isoformat()
    return _as_text(value)


def phase10_reminder_type_label(reminder_type: Any) -> str:
    key = _as_text(reminder_type).lower()
    return REMINDER_TYPE_LABELS.get(key, _as_text(reminder_type) or "Süreç Bilgilendirmesi")


def phase10_channel_label(channel: Any) -> str:
    key = _as_text(channel).lower()
    return CHANNEL_LABELS.get(key, _as_text(channel) or "Sistem Bildirimi")


def phase10_status_label(status: Any) -> str:
    key = _as_text(status).lower()
    return STATUS_LABELS.get(key, _as_text(status) or "Süreç Durumu Belirtilmedi")


def phase10_due_status_label(status: Any) -> str:
    key = _as_text(status).lower()
    return DUE_STATUS_LABELS.get(key, _as_text(status) or "Süreç Takipte")


def phase10_clean_text(value: Any) -> str:
    text = _as_text(value)
    replacements = {
        "workflow state": "süreç durumu",
        "workflow": "süreç",
        "endpoint": "bağlantı",
        "debug": "teknik kayıt",
        "exception": "hata kaydı",
        "traceback": "hata izi",
        "authorized_scope": "yetki kapsamı",
        "phase sync": "süreç eşleşmesi",
        "raw json": "ham veri",
        "json": "veri",
        "stacktrace": "hata izi",
    }
    for old, new in replacements.items():
        text = text.replace(old, new).replace(old.upper(), new).replace(old.title(), new)
    return text


def phase10_contains_technical_language(value: Any) -> bool:
    text = _as_text(value).lower()
    return any(word in text for word in TECHNICAL_WORDS)


def phase10_is_weekend(day: date | datetime | str | None = None) -> bool:
    parsed = _as_date(day) or date.today()
    return parsed.weekday() >= 5


def phase10_due_status(row: dict[str, Any], today: date | datetime | str | None = None, due_soon_days: int = 3) -> str:
    status = _as_text(row.get("status") or row.get("assignment_status") or row.get("durum")).lower()
    if status in {"completed", "done", "tamamlandi", "tamamlandı", "published", "closed"}:
        return "completed"
    due_date = _as_date(row.get("due_date") or row.get("deadline") or row.get("end_date") or row.get("bitis_tarihi"))
    if not due_date:
        return "not_due"
    current = _as_date(today) or date.today()
    delta = (due_date - current).days
    if delta < 0:
        return "overdue"
    if delta == 0:
        return "due_today"
    if delta <= int(due_soon_days or 3):
        return "due_soon"
    return "not_due"


def normalize_phase10_reminder(row: dict[str, Any]) -> dict[str, Any]:
    reminder_type = _as_text(row.get("reminder_type") or row.get("type") or row.get("tur") or "process_info").lower()
    if reminder_type not in REMINDER_TYPE_LABELS:
        reminder_type = "process_info"
    channel = _as_text(row.get("channel") or row.get("kanal") or "notification").lower()
    if channel not in CHANNEL_LABELS:
        channel = "notification"
    subject = phase10_clean_text(row.get("subject") or row.get("baslik") or phase10_reminder_type_label(reminder_type))
    message = phase10_clean_text(row.get("message") or row.get("mesaj") or "Performans sürecinde takip gerektiren bir kayıt bulunmaktadır.")
    weekday_only = _as_bool(row.get("weekday_only"), True)
    due_status = phase10_due_status(row, row.get("today"), _as_int(row.get("due_soon_days"), 3) or 3)
    status = _as_text(row.get("status") or "planned").lower()
    if due_status == "overdue":
        status = "overdue"
    return {
        "employee_id": _as_int(row.get("employee_id") or row.get("personel_id")),
        "evaluator_id": _as_int(row.get("evaluator_id") or row.get("manager_id") or row.get("amir_id")),
        "period_id": _as_int(row.get("period_id") or row.get("performance_period_id") or row.get("donem_id")),
        "assignment_id": _as_int(row.get("assignment_id") or row.get("task_id") or row.get("gorev_id")),
        "reminder_type": reminder_type,
        "reminder_type_label": phase10_reminder_type_label(reminder_type),
        "channel": channel,
        "channel_label": phase10_channel_label(channel),
        "subject": subject,
        "message": message,
        "due_date": _as_date_text(row.get("due_date") or row.get("deadline") or row.get("end_date")),
        "due_status": due_status,
        "due_status_label": phase10_due_status_label(due_status),
        "weekday_only": weekday_only,
        "requires_log": _as_bool(row.get("requires_log"), True),
        "status": status,
        "status_label": phase10_status_label(status),
    }


def validate_phase10_reminder(row: dict[str, Any]) -> Phase10ReminderValidation:
    normalized = normalize_phase10_reminder(row)
    errors: list[str] = []
    warnings: list[str] = []
    if not normalized.get("reminder_type"):
        errors.append("Hatırlatma türü zorunludur.")
    if not normalized.get("subject"):
        errors.append("Hatırlatma başlığı zorunludur.")
    if not normalized.get("message"):
        errors.append("Hatırlatma mesajı zorunludur.")
    if normalized.get("channel") == "mail" and not normalized.get("requires_log"):
        warnings.append("E-posta hatırlatmaları için log kaydı önerilir.")
    if phase10_contains_technical_language(normalized.get("subject")) or phase10_contains_technical_language(normalized.get("message")):
        warnings.append("Hatırlatma metninde teknik ifade temizlenmelidir.")
    return Phase10ReminderValidation(ok=not errors, errors=errors, warnings=warnings, normalized=normalized)


def phase10_reminder_decision(row: dict[str, Any], today: date | datetime | str | None = None) -> Phase10ReminderDecision:
    normalized = normalize_phase10_reminder(row)
    weekday_only = _as_bool(normalized.get("weekday_only"), True)
    channel = _as_text(normalized.get("channel") or "notification")
    requires_log = _as_bool(normalized.get("requires_log"), True)
    if weekday_only and phase10_is_weekend(today):
        return Phase10ReminderDecision(
            should_send=False,
            status="skipped_weekend",
            status_label=phase10_status_label("skipped_weekend"),
            reason="Hafta sonu gönderim kuralı aktif olduğu için otomatik hatırlatma gönderilmedi.",
            channel=channel,
            weekday_only=True,
            requires_log=requires_log,
        )
    due_status = normalized.get("due_status")
    if due_status in {"due_soon", "due_today", "overdue"} or normalized.get("reminder_type") in {"low_score_approval", "publish_preapproval", "manager_delay"}:
        return Phase10ReminderDecision(
            should_send=True,
            status="ready",
            status_label=phase10_status_label("ready"),
            reason=phase10_due_status_label(due_status),
            channel=channel,
            weekday_only=weekday_only,
            requires_log=requires_log,
        )
    return Phase10ReminderDecision(
        should_send=False,
        status="planned",
        status_label=phase10_status_label("planned"),
        reason="Süreç takipte; henüz otomatik hatırlatma eşiğine gelmedi.",
        channel=channel,
        weekday_only=weekday_only,
        requires_log=requires_log,
    )


def phase10_build_log_payload(row: dict[str, Any], today: date | datetime | str | None = None) -> dict[str, Any]:
    normalized = normalize_phase10_reminder(row)
    decision = phase10_reminder_decision(row, today)
    return {
        **normalized,
        "decision": decision.as_dict(),
        "log_status": decision.status,
        "log_status_label": decision.status_label,
        "created_at": datetime.utcnow().isoformat(timespec="seconds"),
    }


def phase10_delayed_evaluator_summary(tasks: Iterable[dict[str, Any]], today: date | datetime | str | None = None, due_soon_days: int = 3) -> list[dict[str, Any]]:
    buckets: dict[int | None, dict[str, Any]] = {}
    for task in tasks or []:
        evaluator_id = _as_int(task.get("evaluator_id") or task.get("manager_id") or task.get("amir_id"))
        name = _as_text(task.get("evaluator_name") or task.get("manager_name") or task.get("amir_adi") or "Amir")
        bucket = buckets.setdefault(evaluator_id, {"name": name, "pending": 0, "overdue": 0, "due_today": 0, "due_soon": 0})
        due_status = phase10_due_status(task, today, due_soon_days)
        if due_status != "completed":
            bucket["pending"] += 1
        if due_status == "overdue":
            bucket["overdue"] += 1
        elif due_status == "due_today":
            bucket["due_today"] += 1
        elif due_status == "due_soon":
            bucket["due_soon"] += 1
    result = []
    for evaluator_id, item in buckets.items():
        if item["overdue"]:
            status_label = "Aksatan Amir / Geciken Görev Var"
        elif item["due_today"]:
            status_label = "Bugün Tamamlanması Gereken Görev Var"
        elif item["due_soon"]:
            status_label = "Son Tarihi Yaklaşan Görev Var"
        else:
            status_label = "Süreç Takipte"
        result.append(Phase10DelayedEvaluatorSummary(
            evaluator_id=evaluator_id,
            evaluator_name=item["name"],
            pending_count=item["pending"],
            overdue_count=item["overdue"],
            due_today_count=item["due_today"],
            due_soon_count=item["due_soon"],
            status_label=status_label,
        ).as_dict())
    return sorted(result, key=lambda x: (x["overdue_count"], x["due_today_count"], x["due_soon_count"]), reverse=True)


def phase10_contract() -> dict[str, Any]:
    return {
        "version": BYS360_PERFORMANCE_COMPLETION_PHASE10_VERSION,
        "markers": {
            "center": BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_CENTER,
            "weekday_only": BYS360_PERFORMANCE_COMPLETION_PHASE10_WEEKDAY_ONLY,
            "delayed_evaluator_report": BYS360_PERFORMANCE_COMPLETION_PHASE10_DELAYED_EVALUATOR_REPORT,
            "mail_log_required": BYS360_PERFORMANCE_COMPLETION_PHASE10_MAIL_LOG_REQUIRED,
            "no_admin_decision": BYS360_PERFORMANCE_COMPLETION_PHASE10_NO_ADMIN_DECISION,
            "technical_language_clean": BYS360_PERFORMANCE_COMPLETION_PHASE10_TECHNICAL_LANGUAGE_CLEAN,
        },
        "table": PHASE10_TABLE_NAME,
        "settings": [
            {"module_key": m, "setting_key": k, "label": label, "value_type": t, "default_value": v, "description": d}
            for m, k, label, t, v, d in PHASE10_SETTING_ROWS
        ],
        "rules": [
            "Bekleyen değerlendirme görevleri için otomatik hatırlatma kararı tek merkezden verilir.",
            "Hafta sonu gönderim kuralı tüm performans hatırlatma türleri için ortak uygulanır.",
            "Geciken görevler amir bazlı aksatan amir raporuna dönüşür.",
            "Hatırlatma ve süreç bildirimleri otomatik puan, ceza veya idari karar üretmez.",
            "Gönderilen veya hafta sonu nedeniyle atlanan bildirimler loglanır.",
        ],
    }


# BYS360 DEFECT AR: ensure_phase10_tables()/seed_phase10_reminder_settings()
# kaldirildi -- repo genelinde (app/, tests/, scripts/) hicbir gercek
# cagirani yoktu (yalnizca artik silinmis olan reminder_notification_service.py
# bridge dosyasi re-export ediyordu, o da hicbir yerden import edilmiyordu).
# Canli "Hatirlatmalar" ozelligi app/performance/meeting_p3_reminders_routes.py
# -> app/services/performance/meeting_p3_reminders.py'nin kendi
# ensure_reminder_queue_table()/ensure_overdue_snapshot_table()'i uzerinden
# calisir; bu dosyanin geri kalani degismedi.
