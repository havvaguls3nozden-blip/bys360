# -*- coding: utf-8 -*-

"""BYS360 Maintenance Faz 6 - SQL / performans indeks sozlesmeleri.

Bu modul veritabaninda otomatik DDL calistirmaz. Canli omurgadaki yogun
okuma/yazma yuzeyleri icin onerilen indeksleri merkezi katalogda tutar ve
istege bagli SQL metni uretir. Uretilecek SQL DBA/admin kontrolunden sonra
manuel calistirilmalidir.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class RecommendedIndex:
    module: str
    table: str
    name: str
    columns: tuple[str, ...]
    reason: str
    where: str | None = None
    unique: bool = False

    def to_sql(self, *, concurrently: bool = False) -> str:
        unique_sql = "UNIQUE " if self.unique else ""
        concurrently_sql = " CONCURRENTLY" if concurrently else ""
        columns_sql = ", ".join(self.columns)
        where_sql = f" WHERE {self.where}" if self.where else ""
        return f"CREATE {unique_sql}INDEX IF NOT EXISTS {self.name}{concurrently_sql} ON {self.table} ({columns_sql}){where_sql};"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


# Canli omurga: kimlik/yetki/ayarlar, personel-izin-vekalet, performans,
# iletisim/anket/geri bildirim ve AI karar destek yuzeyleri.
RECOMMENDED_INDEXES: tuple[RecommendedIndex, ...] = (
    # Kimlik / yetki / ayarlar
    RecommendedIndex("kimlik", "users", "ix_phase6_users_active_unit_role", ("is_active", "birim", "unvan"), "Personel listeleri, rol/birim filtreleri ve yonetsel ekranlar."),
    RecommendedIndex("kimlik", "users", "ix_phase6_users_sicil_no", ("sicil_no",), "Sicil no ile arama ve personel eslestirme."),
    RecommendedIndex("kimlik", "organization_units", "ix_phase6_org_units_parent_active", ("parent_id", "is_active"), "Birim agaci ve alt birim filtreleri."),
    RecommendedIndex("ayarlar", "system_settings", "ix_phase6_system_settings_key_active", ("setting_key", "is_active"), "Sistem ayarı anahtar okuması."),
    RecommendedIndex("ayarlar", "module_settings", "ix_phase6_module_settings_module_key", ("module_key", "setting_key"), "Modül bazlı ayar okuma/yazma."),
    RecommendedIndex("ayarlar", "settings_change_logs", "ix_phase6_settings_logs_created", ("created_at", "actor_user_id"), "Ayar değişiklik geçmişi ve denetim izi."),
    RecommendedIndex("yetki", "user_menu_permissions", "ix_phase6_menu_permissions_user_visible", ("user_id", "is_visible"), "Kisi bazli menu gorunurlugu."),
    RecommendedIndex("yetki", "role_menu_defaults", "ix_phase6_role_menu_role_key", ("role_name", "menu_key"), "Rol varsayilan menu cozumu."),
    RecommendedIndex("destek", "support_tickets", "ix_phase6_support_tickets_status_updated", ("status", "updated_at"), "Yardim merkezi is listeleri."),
    RecommendedIndex("denetim", "audit_logs", "ix_phase6_audit_logs_user_created", ("user_id", "created_at"), "Audit log kullanici/tarih filtreleri."),

    # Personel / izin / vekalet
    RecommendedIndex("personel", "employee_org_assignment_history", "ix_phase6_employee_assignment_user_current", ("user_id", "is_current"), "Guncel personel-birim eslestirmesi."),
    RecommendedIndex("izin", "leave_requests", "ix_phase6_leave_requests_user_status_dates", ("user_id", "status", "start_date", "end_date"), "Kullanici izin gecmisi ve durum filtreleri."),
    RecommendedIndex("izin", "personnel_leaves", "ix_phase6_personnel_leaves_period_user", ("period_id", "user_id"), "Performans donemi izin/rapor etkisi."),
    RecommendedIndex("izin", "attendance_events", "ix_phase6_attendance_events_user_date", ("user_id", "event_date"), "Devamsizlik gun bazli kontrol."),
    RecommendedIndex("vekalet", "delegation_assignments", "ix_phase6_delegation_active_manager", ("delegator_id", "status", "start_date", "end_date"), "Izinli amir gorev devri ve aktif vekalet sorgulari."),

    # Performans
    RecommendedIndex("performans", "performance_periods", "ix_phase6_periods_active_dates", ("is_active", "start_date", "end_date"), "Aktif donem ve takvim penceresi."),
    RecommendedIndex("performans", "evaluation_assignments", "ix_phase6_eval_assignments_evaluator_status", ("evaluator_id", "status", "period_id"), "Amir gorev listeleri."),
    RecommendedIndex("performans", "evaluation_assignments", "ix_phase6_eval_assignments_employee_period", ("employee_id", "period_id", "manager_level"), "Personel bazli gorev zinciri."),
    RecommendedIndex("performans", "performance_evaluations", "ix_phase6_perf_eval_period_employee", ("period_id", "employee_id"), "Donem/personel degerlendirme bulma."),
    RecommendedIndex("performans", "performance_evaluations", "ix_phase6_perf_eval_l1_status", ("level_1_evaluator_id", "workflow_status"), "1. amir is akisi filtreleri."),
    RecommendedIndex("performans", "performance_evaluations", "ix_phase6_perf_eval_l2_status", ("level_2_evaluator_id", "workflow_status"), "2. amir is akisi filtreleri."),
    RecommendedIndex("performans", "performance_evaluations", "ix_phase6_perf_eval_l3_status", ("level_3_evaluator_id", "workflow_status"), "3. amir gorus/puan is akisi filtreleri."),
    RecommendedIndex("performans", "performance_result_snapshots", "ix_phase6_result_snapshots_period_unit", ("period_id", "organization_unit_id"), "Yayinlanmis sonuc ve birim raporlari."),
    RecommendedIndex("performans", "assignment_audit_logs", "ix_phase6_assignment_audit_period_created", ("period_id", "created_at"), "Atama denetim izi."),

    # Geri bildirim / nabiz
    RecommendedIndex("geri_bildirim", "feedback_campaigns", "ix_phase6_feedback_campaigns_status_dates", ("status", "start_date", "end_date"), "Aktif kampanya ve nabiz listeleri."),
    RecommendedIndex("geri_bildirim", "feedback_campaign_assignments", "ix_phase6_feedback_assignments_user_campaign", ("user_id", "campaign_id"), "Kullaniciya gorunen kampanya cozumu."),
    RecommendedIndex("geri_bildirim", "feedback_submissions", "ix_phase6_feedback_submissions_campaign_unit", ("campaign_id", "organization_unit_id"), "Kampanya sonuc/birim analizi."),
    RecommendedIndex("geri_bildirim", "feedback_pulse_entries", "ix_phase6_feedback_pulse_unit_date", ("organization_unit_id", "entry_date"), "Nabiz trend paneli."),
    RecommendedIndex("geri_bildirim", "feedback_action_plans", "ix_phase6_feedback_actions_status_due", ("status", "due_date"), "Aksiyon plani takip listeleri."),

    # Iletisim / anket
    RecommendedIndex("iletisim", "message_threads", "ix_phase6_message_threads_updated", ("updated_at", "created_by_user_id"), "Mesaj kutusu son hareket siralamasi."),
    RecommendedIndex("iletisim", "message_thread_participants", "ix_phase6_thread_participants_user_thread", ("user_id", "thread_id"), "Kullanicinin mesaj thread erisimi."),
    RecommendedIndex("iletisim", "messages", "ix_phase6_messages_thread_created", ("thread_id", "created_at"), "Mesaj akisi ve sonsuz kaydirma."),
    RecommendedIndex("iletisim", "message_attachments", "ix_phase6_message_attachments_message", ("message_id", "created_at"), "Mesaj ekleri ve galeri listeleri."),
    RecommendedIndex("anket", "surveys", "ix_phase6_surveys_status_dates", ("status", "start_date", "end_date"), "Aktif anket listesi."),
    RecommendedIndex("anket", "survey_assignments", "ix_phase6_survey_assignments_user_survey", ("user_id", "survey_id"), "Kullaniciya atanan anketler."),
    RecommendedIndex("anket", "survey_responses", "ix_phase6_survey_responses_survey_user", ("survey_id", "user_id"), "Anket cevap/katilim kontrolu."),

    # AI karar destek
    RecommendedIndex("ai", "ai_request_logs", "ix_phase6_ai_request_logs_user_created", ("user_id", "created_at"), "AI islem loglari kullanici/tarih filtreleri."),
    RecommendedIndex("ai", "ai_request_logs", "ix_phase6_ai_request_logs_status_module", ("status", "module_type", "feature_type"), "AI log izleme ve hata paneli."),
    RecommendedIndex("ai", "ai_recommendations", "ix_phase6_ai_recommendations_status_severity", ("status", "severity", "module_type"), "AI oneri is listesi."),
    RecommendedIndex("ai", "ai_summary_cache", "ix_phase6_ai_summary_cache_expires", ("module_type", "target_table", "target_id", "summary_kind", "expires_at"), "AI ozet cache cozumleme."),
)


CRITICAL_QUERY_SURFACES: tuple[str, ...] = (
    "app/services/performance_service.py",
    "app/services/performance_v2/reporting_workspace.py",
    "app/services/performance_snapshot_service.py",
    "app/services/feedback_service.py",
    "app/services/message_service.py",
    "app/services/leave_delegation_service.py",
    "app/services/settings_service.py",
    "app/services/decision_support_service.py",
    "app/services/query_health/assignment_board.py",
    "app/services/query_health/dashboard.py",
    "app/services/query_health/workflow_meta.py",
)


def iter_recommended_indexes(module: str | None = None) -> Iterable[RecommendedIndex]:
    for item in RECOMMENDED_INDEXES:
        if module is None or item.module == module:
            yield item


def build_postgresql_index_sql(*, concurrently: bool = False) -> str:
    header = [
        "-- BYS360 Maintenance Faz 6 - onerilen indeksler",
        "-- Otomatik calistirilmaz. Canli DB icin once yedek + DBA/Admin kontrolu onerilir.",
        "-- CREATE INDEX CONCURRENTLY kullanilacaksa transaction icinde calistirmayin.",
        "",
    ]
    body: list[str] = []
    for item in RECOMMENDED_INDEXES:
        body.append(f"-- [{item.module}] {item.reason}")
        body.append(item.to_sql(concurrently=concurrently))
        body.append("")
    return "\n".join(header + body)


def build_index_manifest() -> list[dict[str, object]]:
    return [item.to_dict() for item in RECOMMENDED_INDEXES]
