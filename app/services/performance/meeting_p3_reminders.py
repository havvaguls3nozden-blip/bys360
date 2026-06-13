# -*- coding: utf-8 -*-
from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

"""BYS360 Toplantı Kararları — Faz 9 otomatik hatırlatma servisi.

Bu servis, toplantı kararlarından çıkan otomatik hatırlatma, aksatan amir görünürlüğü,
sistem içi bildirim ve mail log disiplinini güvenli biçimde hazırlar.

Faz 9 bilinçli olarak e-posta göndermez; gönderim için denetlenebilir kuyruk, ayar,
mail log bağlantısı ve aksatan amir özetini kurar.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

P3_REMINDERS_VERSION = "2026-04-30-meeting-faz9-reminders"

P3_REQUIRED_SETTINGS = {
    "performance_auto_reminders_enabled": {"label": "Performans otomatik hatırlatma aktif", "value": "true", "description": "Bekleyen performans görevleri için kontrollü hatırlatma kuyruğu oluşturulmasını sağlar."},
    "performance_reminder_days_before_deadline": {"label": "Son tarih öncesi hatırlatma günü", "value": "3", "value_type": "integer", "description": "Son tarihe kaç gün kala hatırlatma üretileceğini belirler."},
    "performance_overdue_manager_enabled": {"label": "Aksatan amir tespiti aktif", "value": "true", "description": "Son tarihi geçmiş tamamlanmamış görevleri aksatan amir raporuna dahil eder."},
    "performance_overdue_manager_report_enabled": {"label": "Aksatan amir raporu aktif", "value": "true", "description": "Geciken değerlendirme görevlerini yönetici görünürlüğüne hazırlar."},
    "performance_system_notification_reminders_enabled": {"label": "Sistem içi hatırlatma bildirimi aktif", "value": "true", "description": "Hatırlatmaların sistem içi bildirim olarak üretilebilmesini sağlar."},
    "performance_email_reminders_enabled": {"label": "E-posta hatırlatma altyapısı aktif", "value": "false", "description": "E-posta gönderimini ayara bağlar; varsayılan kapalıdır, canlıda bilinçli açılır."},
    "performance_reminder_mail_log_required": {"label": "Hatırlatma mail log zorunluluğu", "value": "true", "description": "E-posta hatırlatmalarının mail_logs ile izlenebilir olmasını zorunlu kılar."},
    "performance_reminder_no_sensitive_content": {"label": "Hatırlatmalarda hassas içerik gösterilmez", "value": "true", "description": "Hatırlatma metinlerinde puan, amir görüşü ve personel özel değerlendirme içeriği yer almaz."},
    "performance_reminder_manager_scope": {"label": "Hatırlatma görünürlüğü yönetici kapsamıyla sınırlı", "value": "true", "description": "Aksatan amir ve bekleyen görev görünürlüğünü rol/kapsam yetkisiyle sınırlar."},
    "performance_reminder_scheduler_ready": {"label": "Zamanlanmış iş hazırlığı tamamlandı", "value": "true", "description": "Canlıda zamanlanmış görev ile tetiklenebilecek hatırlatma altyapısını işaretler."},
}

P3_REMINDER_QUEUE_TABLE = "performance_reminder_queue"
P3_OVERDUE_SNAPSHOT_TABLE = "performance_overdue_manager_snapshots"

P3_REMINDER_REQUIRED_COLUMNS = {"id", "assignment_id", "period_id", "manager_user_id", "employee_user_id", "reminder_type", "channel", "due_at", "status", "title", "message", "created_by", "created_at", "sent_at", "mail_log_id", "notification_id"}
P3_OVERDUE_REQUIRED_COLUMNS = {"id", "period_id", "manager_user_id", "overdue_count", "oldest_due_at", "scope_label", "created_by", "created_at"}

P3_REMINDER_TYPES = [
    {"value": "deadline_approaching", "label": "Son Tarih Yaklaşıyor", "description": "Değerlendirme görevi son tarihinden önce hatırlatma üretir."},
    {"value": "overdue_assignment", "label": "Geciken Değerlendirme", "description": "Son tarihi geçmiş tamamlanmamış görevleri aksatan amir takibine alır."},
    {"value": "manager_summary", "label": "Yönetici Özeti", "description": "Yöneticiye kendi kapsamındaki bekleyen/geciken görev özetini hazırlar."},
    {"value": "period_closing", "label": "Dönem Kapanış Hatırlatması", "description": "Dönem kapanışı yaklaşırken ilgili amirleri ve yetkilileri uyarır."},
]

@dataclass(slots=True)
class P3ReminderResult:
    ok: bool
    version: str
    settings_seeded: int = 0
    tables_ready: int = 0
    checks_passed: int = 0
    message: str = ""
    warnings: list[str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "version": self.version, "settings_seeded": self.settings_seeded, "tables_ready": self.tables_ready, "checks_passed": self.checks_passed, "message": self.message, "warnings": list(self.warnings or [])}

def _dialect() -> str:
    try:
        return db.engine.dialect.name
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/meeting_p3_reminders.py | line=67")
        return "unknown"

def _has_table(table_name: str) -> bool:
    try:
        return bool(inspect(db.engine).has_table(table_name))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/meeting_p3_reminders.py | line=73")
        return False

def _columns(table_name: str) -> set[str]:
    try:
        return {col["name"] for col in inspect(db.engine).get_columns(table_name)}
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/meeting_p3_reminders.py | line=79")
        return set()

def _scalar(sql: str, params: dict[str, Any] | None = None, default: Any = None) -> Any:
    try:
        return db.session.execute(text(sql), params or {}).scalar()
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/meeting_p3_reminders.py | line=85")
        return default

def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in db.session.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/meeting_p3_reminders.py | line=91")
        return []

def _setting_exists(setting_key: str) -> bool:
    if not _has_table("module_settings"):
        return False
    return bool(_scalar("""SELECT id FROM module_settings WHERE module_key='performance' AND setting_key=:setting_key LIMIT 1""", {"setting_key": setting_key}))

def _id_column_sql() -> str:
    if _dialect() == "postgresql":
        return "id SERIAL PRIMARY KEY"
    return "id INTEGER PRIMARY KEY AUTOINCREMENT"

def ensure_p3_settings() -> int:
    if not _has_table("module_settings"):
        return 0
    seeded = 0
    for key, payload in P3_REQUIRED_SETTINGS.items():
        if _setting_exists(key):
            continue
        db.session.execute(text("""
            INSERT INTO module_settings
                (module_key, setting_key, label, value_text, value_type, description, is_active, created_at, updated_at)
            VALUES
                ('performance', :key, :label, :value, :value_type, :description, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """), {"key": key, "label": payload["label"], "value": payload["value"], "value_type": payload.get("value_type", "boolean"), "description": payload["description"]})
        seeded += 1
    return seeded

def ensure_reminder_queue_table() -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if _has_table(P3_REMINDER_QUEUE_TABLE):
        return True, warnings
    try:
        db.session.execute(text(f"""
            CREATE TABLE {P3_REMINDER_QUEUE_TABLE} (
                {_id_column_sql()}, assignment_id INTEGER, period_id INTEGER, manager_user_id INTEGER,
                employee_user_id INTEGER, reminder_type VARCHAR(80) NOT NULL, channel VARCHAR(40) NOT NULL DEFAULT 'system',
                due_at TIMESTAMP, status VARCHAR(40) NOT NULL DEFAULT 'pending', title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL, created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP, mail_log_id INTEGER, notification_id INTEGER
            )
        """))
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback(); warnings.append(f"Hatırlatma kuyruğu tablosu oluşturulamadı: {exc.__class__.__name__}")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/meeting_p3_reminders.py | line=137")
        db.session.rollback(); warnings.append(f"Hatırlatma kuyruğu tablosu oluşturulamadı: {exc}")
    return _has_table(P3_REMINDER_QUEUE_TABLE), warnings

def ensure_overdue_snapshot_table() -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if _has_table(P3_OVERDUE_SNAPSHOT_TABLE):
        return True, warnings
    try:
        db.session.execute(text(f"""
            CREATE TABLE {P3_OVERDUE_SNAPSHOT_TABLE} (
                {_id_column_sql()}, period_id INTEGER, manager_user_id INTEGER NOT NULL,
                overdue_count INTEGER NOT NULL DEFAULT 0, oldest_due_at TIMESTAMP, scope_label VARCHAR(255),
                created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback(); warnings.append(f"Aksatan amir özet tablosu oluşturulamadı: {exc.__class__.__name__}")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/meeting_p3_reminders.py | line=156")
        db.session.rollback(); warnings.append(f"Aksatan amir özet tablosu oluşturulamadı: {exc}")
    return _has_table(P3_OVERDUE_SNAPSHOT_TABLE), warnings

def _existing_live_tables() -> dict[str, bool]:
    return {"evaluation_assignments": _has_table("evaluation_assignments"), "performance_periods": _has_table("performance_periods"), "notifications": _has_table("notifications"), "mail_logs": _has_table("mail_logs"), "module_settings": _has_table("module_settings")}

def p3_status_checks() -> list[dict[str, Any]]:
    reminder_cols = _columns(P3_REMINDER_QUEUE_TABLE) if _has_table(P3_REMINDER_QUEUE_TABLE) else set()
    overdue_cols = _columns(P3_OVERDUE_SNAPSHOT_TABLE) if _has_table(P3_OVERDUE_SNAPSHOT_TABLE) else set()
    live_tables = _existing_live_tables()
    p2_ready = _setting_exists("performance_interim_notes_enabled") and _has_table("performance_interim_notes")
    checks = [
        ("p3_auto_reminder_setting", "Otomatik hatırlatma ana ayarı hazır.", _setting_exists("performance_auto_reminders_enabled")),
        ("p3_deadline_window_setting", "Son tarih öncesi hatırlatma günü ayarı hazır.", _setting_exists("performance_reminder_days_before_deadline")),
        ("p3_reminder_queue", "Hatırlatma kuyruğu tablosu hazır.", _has_table(P3_REMINDER_QUEUE_TABLE)),
        ("p3_reminder_queue_columns", "Hatırlatma kuyruğunda görev, amir, kanal, durum, mail log ve bildirim alanları var.", P3_REMINDER_REQUIRED_COLUMNS.issubset(reminder_cols)),
        ("p3_overdue_setting", "Aksatan amir tespiti ayarı hazır.", _setting_exists("performance_overdue_manager_enabled")),
        ("p3_overdue_snapshot", "Aksatan amir özet tablosu hazır.", _has_table(P3_OVERDUE_SNAPSHOT_TABLE)),
        ("p3_overdue_columns", "Aksatan amir özetinde amir, dönem, sayı ve en eski gecikme alanları var.", P3_OVERDUE_REQUIRED_COLUMNS.issubset(overdue_cols)),
        ("p3_system_notification", "Sistem içi bildirim altyapısı ayara bağlandı.", _setting_exists("performance_system_notification_reminders_enabled") and live_tables["notifications"]),
        ("p3_email_log", "E-posta hatırlatma mail log disiplinine bağlandı.", _setting_exists("performance_email_reminders_enabled") and _setting_exists("performance_reminder_mail_log_required") and live_tables["mail_logs"]),
        ("p3_no_sensitive_content", "Hatırlatma metinlerinde puan/görüş gibi hassas içerik gösterilmeyecek.", _setting_exists("performance_reminder_no_sensitive_content")),
        ("p3_manager_scope", "Aksatan amir görünürlüğü yönetici kapsamıyla sınırlı.", _setting_exists("performance_reminder_manager_scope")),
        ("p3_scheduler_ready", "Zamanlanmış iş tetikleme hazırlığı işaretlendi.", _setting_exists("performance_reminder_scheduler_ready")),
        ("p3_assignment_source", "Bekleyen görev kaynağı canlı omurgada mevcut.", live_tables["evaluation_assignments"]),
        ("p3_p2_dependency", "Faz 8 arşiv/ara not altyapısı korunuyor.", p2_ready),
    ]
    return [{"code": code, "title": title, "ok": bool(ok), "status": "Hazır" if ok else "Kontrol gerekli"} for code, title, ok in checks]

def p3_summary_cards() -> list[dict[str, Any]]:
    checks = p3_status_checks()
    queue_count = _scalar(f"SELECT COUNT(*) FROM {P3_REMINDER_QUEUE_TABLE}", default=0) if _has_table(P3_REMINDER_QUEUE_TABLE) else 0
    pending_count = _scalar(f"SELECT COUNT(*) FROM {P3_REMINDER_QUEUE_TABLE} WHERE status='pending'", default=0) if _has_table(P3_REMINDER_QUEUE_TABLE) else 0
    overdue_count = _scalar(f"SELECT COALESCE(SUM(overdue_count),0) FROM {P3_OVERDUE_SNAPSHOT_TABLE}", default=0) if _has_table(P3_OVERDUE_SNAPSHOT_TABLE) else 0
    return [
        {"label": "Faz 9 Kontrol", "value": f"{sum(1 for item in checks if item['ok'])}/{len(checks)}", "note": "Hazır olan hatırlatma başlığı"},
        {"label": "Hatırlatma Kuyruğu", "value": str(queue_count or 0), "note": "Toplam kuyruk kaydı"},
        {"label": "Bekleyen Hatırlatma", "value": str(pending_count or 0), "note": "Gönderim bekleyen kayıt"},
        {"label": "Aksayan Görev", "value": str(overdue_count or 0), "note": "Özetlenen gecikme adedi"},
    ]

def seed_demo_reminder(actor_user_id: int | None = None) -> int:
    if not _has_table(P3_REMINDER_QUEUE_TABLE):
        return 0
    title = "Performans değerlendirme hatırlatma altyapısı hazır"
    existing = _scalar(f"SELECT id FROM {P3_REMINDER_QUEUE_TABLE} WHERE reminder_type='manager_summary' AND title=:title LIMIT 1", {"title": title})
    if existing:
        return 0
    db.session.execute(text(f"""
        INSERT INTO {P3_REMINDER_QUEUE_TABLE}
            (reminder_type, channel, status, title, message, created_by, created_at)
        VALUES
            ('manager_summary', 'system', 'draft', :title, :message, :created_by, CURRENT_TIMESTAMP)
    """), {"title": title, "message": "Bu kayıt, hatırlatma kuyruğunun hazır olduğunu gösterir. Puan, amir görüşü veya hassas personel içeriği içermez.", "created_by": actor_user_id})
    return 1

def build_p3_reminders_context(viewer: Any | None = None) -> dict[str, Any]:
    queue_rows = _rows(f"SELECT reminder_type, channel, status, title, created_at, sent_at FROM {P3_REMINDER_QUEUE_TABLE} ORDER BY id DESC LIMIT 10") if _has_table(P3_REMINDER_QUEUE_TABLE) else []
    overdue_rows = _rows(f"SELECT manager_user_id, period_id, overdue_count, oldest_due_at, scope_label, created_at FROM {P3_OVERDUE_SNAPSHOT_TABLE} ORDER BY id DESC LIMIT 10") if _has_table(P3_OVERDUE_SNAPSHOT_TABLE) else []
    return {"title": "Faz 9 Hatırlatma ve Aksatan Amirler", "version": P3_REMINDERS_VERSION, "cards": p3_summary_cards(), "checks": p3_status_checks(), "reminder_types": P3_REMINDER_TYPES, "queue_rows": queue_rows, "overdue_rows": overdue_rows, "settings": _rows("SELECT setting_key, label, value_text, description FROM module_settings WHERE module_key='performance' ORDER BY setting_key") if _has_table("module_settings") else [], "viewer": viewer}

def run_p3_reminders(actor_user_id: int | None = None) -> P3ReminderResult:
    warnings: list[str] = []
    seeded = 0
    try:
        seeded = ensure_p3_settings()
        _, queue_warnings = ensure_reminder_queue_table()
        _, overdue_warnings = ensure_overdue_snapshot_table()
        warnings.extend(queue_warnings); warnings.extend(overdue_warnings)
        seed_demo_reminder(actor_user_id=actor_user_id)
        db.session.commit()
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/meeting_p3_reminders.py | line=228")
        db.session.rollback(); warnings.append(f"Faz 9 hatırlatma hazırlığı tamamlanamadı: {exc}")
    checks = p3_status_checks()
    passed = sum(1 for item in checks if item["ok"])
    tables_ready = int(_has_table(P3_REMINDER_QUEUE_TABLE)) + int(_has_table(P3_OVERDUE_SNAPSHOT_TABLE))
    ok = passed == len(checks)
    return P3ReminderResult(ok=ok, version=P3_REMINDERS_VERSION, settings_seeded=seeded, tables_ready=tables_ready, checks_passed=passed, message="Faz 9 otomatik hatırlatma, aksatan amir ve mail log altyapısı hazır." if ok else "Faz 9 hatırlatma kontrollerinde eksik başlık var.", warnings=warnings)
