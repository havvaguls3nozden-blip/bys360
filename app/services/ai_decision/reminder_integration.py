
"""BYS360 AI Karar Destek Faz 9 hatırlatma entegrasyonu.

Değerlendirme görevleri, bildirim kayıtları ve mail log verilerini kişi içeriği
ve hassas puan detayı açmadan karar destek özetine dönüştürür.

BYS360_AI_DECISION_FAZ9_REMINDER_INTEGRATION
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping

from .reminder_policy import (
    ReminderPolicy,
    build_reminder_policy,
    classify_assignment_status,
    safe_attr,
    summarize_assignments,
    today,
)


def _row_mapping(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if isinstance(row, Mapping):
        return dict(row)
    return {}


def evaluator_delay_distribution(assignments: Iterable[Any], policy: ReminderPolicy | None = None) -> list[dict[str, Any]]:
    """Amir bazında kişi adı açmadan gecikme yoğunluğu üretir."""

    policy = policy or ReminderPolicy()
    grouped: dict[Any, dict[str, Any]] = defaultdict(lambda: {
        "evaluator_id": None,
        "total_count": 0,
        "pending_count": 0,
        "due_soon_count": 0,
        "overdue_count": 0,
        "critical_overdue_count": 0,
        "missing_due_date_count": 0,
    })
    for row in assignments:
        evaluator_id = safe_attr(row, "evaluator_id", "manager_id", "supervisor_id", default="belirtilmedi")
        item = grouped[evaluator_id]
        item["evaluator_id"] = evaluator_id
        item["total_count"] += 1
        classified = classify_assignment_status(row, policy, today())
        if not classified["completed"]:
            item["pending_count"] += 1
        if classified["status_label"] == "Son Tarihi Yaklaşan Değerlendirme":
            item["due_soon_count"] += 1
        if classified["status_label"] in {"Gecikmiş Değerlendirme", "Kritik Gecikmiş Değerlendirme"}:
            item["overdue_count"] += 1
        if classified["risk_level"] == "Kritik":
            item["critical_overdue_count"] += 1
        if classified["status_label"] == "Son Tarih Bilgisi Eksik":
            item["missing_due_date_count"] += 1

    rows = list(grouped.values())
    rows.sort(key=lambda x: (x["critical_overdue_count"], x["overdue_count"], x["due_soon_count"], x["pending_count"]), reverse=True)
    for item in rows:
        if item["critical_overdue_count"]:
            item["risk_level"] = "Kritik"
            item["recommendation"] = "Öncelikli takip ve hatırlatma gerekir."
        elif item["overdue_count"]:
            item["risk_level"] = "Dikkat Gerektirir"
            item["recommendation"] = "Gecikmiş görevler için hatırlatma yapılmalıdır."
        elif item["due_soon_count"]:
            item["risk_level"] = "Yakın Takip"
            item["recommendation"] = "Son tarih yaklaşmadan bilgilendirme yapılmalıdır."
        else:
            item["risk_level"] = "Düzenli"
            item["recommendation"] = "Görev takibi olağan görünüyor."
    return rows


def notification_mail_summary(notifications: Iterable[Any] | None = None, mail_logs: Iterable[Any] | None = None) -> dict[str, Any]:
    notifications = list(notifications or [])
    mail_logs = list(mail_logs or [])
    return {
        "notification_count": len(notifications),
        "mail_log_count": len(mail_logs),
        "communication_note": "Hatırlatma kayıtları bildirim ve e-posta loglarıyla birlikte izlenebilir." if notifications or mail_logs else "Hatırlatma için kayıtlı bildirim veya e-posta logu görünmüyor.",
        "marker": "BYS360_AI_DECISION_FAZ9_NOTIFICATION_MAIL_SUMMARY",
    }


def build_reminder_summary_payload(
    assignments: Iterable[Any],
    notifications: Iterable[Any] | None = None,
    mail_logs: Iterable[Any] | None = None,
    current_user: Any | None = None,
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Genel hatırlatma ve aksatan amir karar destek özetini üretir."""

    policy = build_reminder_policy(settings)
    assignment_rows = list(assignments)
    summary = summarize_assignments(assignment_rows, policy, today())
    evaluator_rows = evaluator_delay_distribution(assignment_rows, policy)[: policy.max_detail_rows]
    communication = notification_mail_summary(notifications, mail_logs)
    attention_items: list[str] = []
    if not policy.enabled:
        attention_items.append("Otomatik hatırlatma ayarı kapalı görünüyor.")
    if summary["critical_overdue_count"]:
        attention_items.append("Kritik gecikmiş değerlendirme görevi bulunuyor.")
    if summary["overdue_count"]:
        attention_items.append("Gecikmiş değerlendirme görevleri için hatırlatma önerilir.")
    if summary["missing_due_date_count"]:
        attention_items.append("Son tarih bilgisi eksik görevler dönem takvimiyle kontrol edilmelidir.")

    return {
        "ok": True,
        "module": "AI Karar Destek Merkezi",
        "scope": "Otomatik Hatırlatma ve Aksatan Amir",
        "summary": summary,
        "evaluator_delay_distribution": evaluator_rows,
        "communication": communication,
        "attention_items": attention_items,
        "privacy_note": "Bu özet kişi adı, puan ve amir görüşü açmadan görev gecikmesi sinyali verir.",
        "safety_note": "Bu çıktı idari karar değildir; süreç takibini kolaylaştıran insan denetimli karar desteğidir.",
        "marker": "BYS360_AI_DECISION_FAZ9_REMINDER_SUMMARY_PAYLOAD",
    }


def build_evaluator_delay_payload(assignments: Iterable[Any], settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    policy = build_reminder_policy(settings)
    rows = evaluator_delay_distribution(assignments, policy)[: policy.max_detail_rows]
    return {
        "ok": True,
        "module": "AI Karar Destek Merkezi",
        "scope": "Aksatan Amir Yoğunluğu",
        "rows": rows,
        "row_count": len(rows),
        "privacy_note": "Liste kişi adı göstermeden amir kimliği ve görev yoğunluğu seviyesinde özet verir.",
        "marker": "BYS360_AI_DECISION_FAZ9_EVALUATOR_DELAY_PAYLOAD",
    }


def build_reminder_action_plan_payload(assignments: Iterable[Any], settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Bildirim/e-posta çalıştırmadan önce insan onaylı takip planı üretir."""

    policy = build_reminder_policy(settings)
    summary = summarize_assignments(assignments, policy, today())
    actions = []
    if summary["critical_overdue_count"]:
        actions.append("Kritik gecikmiş görevler için yönetsel takip listesi oluşturulmalı.")
    if summary["overdue_count"]:
        actions.append("Gecikmiş görev sahiplerine sistem içi hatırlatma hazırlanmalı.")
    if summary["due_soon_count"]:
        actions.append("Son tarihi yaklaşan görevler için nazik bilgilendirme yapılmalı.")
    if summary["missing_due_date_count"]:
        actions.append("Son tarih bilgisi eksik görevler dönem takvimiyle tamamlanmalı.")
    if not actions:
        actions.append("Ek hatırlatma gerektiren görev görünmüyor.")
    return {
        "ok": True,
        "module": "AI Karar Destek Merkezi",
        "scope": "Hatırlatma Eylem Planı",
        "summary": summary,
        "recommended_actions": actions,
        "email_enabled": policy.send_email_if_enabled,
        "notification_enabled": policy.create_notification_if_enabled,
        "safety_note": "Bu plan otomatik idari işlem oluşturmaz; yetkili kullanıcı kontrolüyle uygulanır.",
        "marker": "BYS360_AI_DECISION_FAZ9_ACTION_PLAN_PAYLOAD",
    }
