"""BYS360 Assistant V2 -- capability registry.

Single source of truth for "what can the assistant actually DO, module by
module" -- capability_key, which module it belongs to, what kind of
operation it is, which real permission_key/menu_key gates it, and which
real, importable function actually serves the read.

This mirrors the exact pattern established by
`app.services.settings.module_registry` (module_key -> ModuleRegistryEntry,
frozen dataclasses, `find_*` completeness helpers, no side effects at import
time). It is an ADDITIVE registry on top of the existing module inventory in
`app.services.settings.module_registry.MODULE_REGISTRY` -- every
`module_key` used below must already exist there; this file does not define
new modules, only the assistant-facing capabilities each existing module
exposes.

Scope of this slice (read-first mandate): every capability registered here
is `read_or_write="read"`. No capability here creates, updates, approves,
deletes, or exports anything -- that is deliberately out of scope until a
later, separately-reviewed phase (see `test_all_capabilities_are_read_only_for_v2`
in the paired completeness test).

`service_handler` is always a dotted path string, never a live import -- the
router/handler layer that will dispatch these (not built in this slice)
resolves it lazily, exactly like `ModuleRegistryEntry.settings_endpoint`
stores an endpoint *name*, not a bound view function. Every path below was
verified importable against this worktree's real source tree; entries that
reuse an existing, already-shipped read function say so in `evidence`.
Entries with no pre-existing, narrow-enough read function point at a new,
thin function added in `app.services.assistant_v2.read_adapters` (see that
module's own docstring for the shared conventions those functions follow:
bounded queries, logged non-silent failure, no authorization inside the
adapter itself).

Three deliberate, reviewed exceptions to the normal `permission_key` pattern
(none of these invent a new authorization mechanism -- each reuses a real,
already-enforced check elsewhere in this codebase):

  - File Center's 3 capabilities (`file_center_*`): File Center predates and
    bypasses the menu-key visibility pipeline entirely -- it has no
    `anchor_menu_key` in MODULE_REGISTRY either, for the exact same reason
    (see app/services/settings/module_registry.py:147's own comment on this
    module: "File Center has no left-sidebar MENU_SECTIONS entry; reached
    via its own nav, gated by can_manage_file_center_settings() instead").
    These entries set `permission_key=None`, `is_self_describing=False`, and
    `extra={"auth_override": "app.file_center.permissions.can_manage_file_center_settings"}`.
    The real gate is enforcing a direct call to that function; this registry
    entry only documents which function that is. No router/handler is built
    in this slice, so nothing calls it yet.

  - `email_automation_summarize_performance_reminder_health`: performance
    reminder mail health is admin-only operational telemetry with no
    dedicated menu_key of its own. Same pattern:
    `permission_key=None`, `extra={"auth_override": "admin_required_role_family"}`,
    meant to be enforced with `app.route_support.ADMIN_FAMILY_ROLES` (the
    exact same role-family constant already used by
    `app.route_support.admin_required` -- no new role set invented).

  - The two `virtual_assistant_discover_*` capabilities: self-describing
    (`is_self_describing=True`, `permission_key=None`). These enumerate what
    exists / what the current user can reach -- they grant no access
    themselves, so they are intentionally not menu-gated, only
    login-gated (a router built later would still require
    `current_user.is_authenticated`).

Everything else below carries a real `permission_key` that is a real,
existing `menu_key` cross-referenced against `app.menu_registry_data_sections.MENU_SECTIONS`
and `app.menu_registry.MENU_SECTIONS`/`ALL_MENU_ITEMS` at the time this file
was written (see each entry's `evidence`).
"""
from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from typing import Any

from app.services.settings.module_registry import MODULE_REGISTRY

logger = logging.getLogger(__name__)

OPERATION_TYPES = frozenset({
    "DISCOVER", "EXPLAIN", "SEARCH", "READ_RECORD", "LIST", "SUMMARIZE",
    "COMPARE", "AGGREGATE", "CROSS_MODULE", "NAVIGATE",
    "CREATE", "UPDATE", "APPROVE", "DELETE", "EXPORT",
})
READ_WRITE_VALUES = frozenset({"read", "write"})
SENSITIVITY_LEVELS = frozenset({"public", "internal", "sensitive", "critical"})


@dataclass(frozen=True)
class AssistantCapabilityEntry:
    capability_key: str
    module_key: str
    display_name: str
    description: str
    intent_tags: tuple[str, ...]
    operation_type: str
    read_or_write: str
    permission_key: str | None
    is_self_describing: bool
    service_handler: str
    sensitivity: str
    audit_required: bool
    source_attribution_label: str | None
    supports_filters: bool = False
    supports_pagination: bool = False
    active: bool = True
    evidence: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


_ADAPTERS = "app.services.assistant_v2.read_adapters"

# ---------------------------------------------------------------------------
# The registry itself, grouped by module_key in the same order as
# app.services.settings.module_registry.MODULE_REGISTRY.
# ---------------------------------------------------------------------------

ASSISTANT_CAPABILITY_REGISTRY: list[AssistantCapabilityEntry] = [
    # ------------------------------------------------------------------
    # personnel_hr
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="personnel_hr_read_personnel_record",
        module_key="personnel_hr",
        display_name="Personel Özlük Kaydı Okuma",
        description="Sicil numarasına göre tek bir personelin temel özlük bilgilerini (ad, soyad, unvan, birim, üst birim, rol, aktiflik) döndürür.",
        intent_tags=("personnel", "hr", "record", "lookup", "sicil"),
        operation_type="READ_RECORD",
        read_or_write="read",
        permission_key="admin_users",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.personnel_hr_read_personnel_record",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Personel Özlük Kaydı",
        supports_filters=False,
        supports_pagination=False,
        evidence=(
            "app/models/core_models.py:37 User; field selection mirrors the "
            "already-shipped app/services/personnel/list_query.py:134 build_personnel_list_row; "
            "permission_key='admin_users' is the real menu_key at app/menu_registry.py:1101"
        ),
    ),
    AssistantCapabilityEntry(
        capability_key="personnel_hr_list_personnel",
        module_key="personnel_hr",
        display_name="Personel Listesi",
        description="Aktif personel kayıtlarını (admin rolü hariç), özlük ekranıyla aynı alan seçimiyle, sınırlı sayıda satır olarak listeler.",
        intent_tags=("personnel", "hr", "list", "directory"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="admin_users",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.personnel_hr_list_personnel",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Personel Listesi",
        supports_filters=True,
        supports_pagination=True,
        evidence=(
            "app/services/personnel/list_query.py:122 build_personnel_list_base_query, "
            ":154 build_personnel_list_rows (reused for row formatting)"
        ),
    ),
    AssistantCapabilityEntry(
        capability_key="personnel_hr_list_pending_leave_requests",
        module_key="personnel_hr",
        display_name="Bekleyen İzin Talepleri",
        description="Durumu 'bekliyor' olan personel izin taleplerini, en yeni başlangıç tarihine göre sınırlı sayıda listeler.",
        intent_tags=("personnel", "hr", "leave", "izin", "pending"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="hr_leave_tracking",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.personnel_hr_list_pending_leave_requests",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="İzin Talebi Kaydı",
        supports_filters=False,
        supports_pagination=True,
        evidence=(
            "app/models/hr_models.py:30 PersonnelLeave, status='bekliyor' "
            "(confirmed against app/templates/hr_leave.html:301); "
            "permission_key='hr_leave_tracking' real menu_key at app/menu_registry.py:1104"
        ),
    ),

    # ------------------------------------------------------------------
    # performance_mgmt
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="performance_mgmt_list_active_periods",
        module_key="performance_mgmt",
        display_name="Aktif Performans Dönemleri",
        description="is_active=True olan performans dönemlerini başlık, tür ve tarih aralığıyla listeler.",
        intent_tags=("performance", "period", "list", "donem"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="performance_reports",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.performance_mgmt_list_active_periods",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Performans Dönemi Kaydı",
        supports_filters=False,
        supports_pagination=True,
        evidence="app/models/performance_models.py:10 PerformancePeriod.is_active; permission_key real menu_key at app/menu_registry.py:1157",
    ),
    AssistantCapabilityEntry(
        capability_key="performance_mgmt_read_period_summary",
        module_key="performance_mgmt",
        display_name="Performans Dönemi Özeti",
        description="Tek bir performans dönemi için temel bilgiler ve o döneme ait değerlendirme sayısını döndürür.",
        intent_tags=("performance", "period", "record", "summary"),
        operation_type="READ_RECORD",
        read_or_write="read",
        permission_key="performance_reports",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.performance_mgmt_read_period_summary",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Performans Dönemi Kaydı",
        evidence="app/models/performance_models.py:10 PerformancePeriod, :205 PerformanceEvaluation.period_id",
    ),
    AssistantCapabilityEntry(
        capability_key="performance_mgmt_list_incomplete_evaluations",
        module_key="performance_mgmt",
        display_name="Tamamlanmamış Değerlendirmeler",
        description="Bir performans dönemi için durumu 'tamamlandı' olmayan değerlendirmeleri, çalışan kimliği (employee_id) ve durumla birlikte listeler.",
        intent_tags=("performance", "evaluation", "incomplete", "tamamlanmamış", "pending"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="performance_reports",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.performance_mgmt_list_incomplete_evaluations",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Performans Değerlendirme Kaydı",
        supports_pagination=True,
        evidence=(
            "app/models/performance_models.py:210 PerformanceEvaluation.employee_id, :230 .status; "
            "'tamamlandi' confirmed as the real completed value at app/performance/publish_helpers.py:18. "
            "Added to support the Phase G cross-module orchestration worked example "
            "(app/services/assistant_v2/cross_module_orchestrator.py): intersected against "
            "personnel_hr_list_personnel's employee ids by that orchestrator, not by this adapter itself."
        ),
    ),
    AssistantCapabilityEntry(
        capability_key="performance_mgmt_summarize_kpi_targets",
        module_key="performance_mgmt",
        display_name="KPI / Hedef Özeti",
        description="Kullanıcının erişim düzeyine göre KPI/Hedef tamamlanma durumunu, riskli hedefleri ve yönetici brifing notlarını özetler.",
        intent_tags=("kpi", "hedef", "target", "risky", "riskli", "strategic", "stratejik"),
        operation_type="AGGREGATE",
        read_or_write="read",
        permission_key="performance_kpi_dashboard",
        is_self_describing=False,
        service_handler="app.services.ai_agent.dashboard_kpi_bridge.build_dashboard_kpi_summary_for_user",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Performans > Stratejik > KPI Dashboard",
        evidence=(
            "Phase G ownership research: the real, live KPI dashboard route is "
            "strategic_performance.dashboard (/strategic-performance), gated by the real, existing "
            "menu key 'performance_kpi_dashboard' (app/menu_registry.py:550), which groups alongside every "
            "other performance_* menu key (:584-590) -- NOT chosen by the dashboard_kpi_bridge.py filename "
            "(explicitly rejected per this project's own instruction not to guess from a filename). "
            "REUSED existing function: app/services/ai_agent/dashboard_kpi_bridge.py:112 "
            "build_dashboard_kpi_summary_for_user() -- already computes exactly this aggregate; no "
            "computation logic duplicated here."
        ),
    ),
    AssistantCapabilityEntry(
        capability_key="performance_mgmt_summarize_evaluation_completion",
        module_key="performance_mgmt",
        display_name="Değerlendirme Tamamlanma Özeti",
        description="Bir performans dönemi için değerlendirme kayıtlarını durum (status) bazında gruplayıp sayar.",
        intent_tags=("performance", "evaluation", "summary", "completion"),
        operation_type="SUMMARIZE",
        read_or_write="read",
        permission_key="performance_kpi_dashboard",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.performance_mgmt_summarize_evaluation_completion",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Değerlendirme Durumu Özeti",
        evidence="app/models/performance_models.py:205 PerformanceEvaluation.status; permission_key real menu_key at app/menu_registry.py:1158",
    ),

    # ------------------------------------------------------------------
    # portal
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="portal_list_recent_posts",
        module_key="portal",
        display_name="Güncel Portal Gönderileri",
        description="Kullanıcının görebileceği, en güncel portal gönderilerini listeler (mevcut görünürlük kurallarıyla).",
        intent_tags=("portal", "feed", "posts", "list"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="portal_feed",
        is_self_describing=False,
        service_handler="app.services.portal_service.visible_posts_for_user",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Portal Gönderisi",
        supports_filters=True,
        supports_pagination=True,
        evidence=(
            "REUSED existing function: app/services/portal_service.py:260 "
            "visible_posts_for_user(user, *, limit=50, author_id=None, group_id=None, wall_owner_id=None) "
            "-- already bounded (default limit=50) and already scoped to the given user's visibility"
        ),
    ),
    AssistantCapabilityEntry(
        capability_key="portal_read_post_detail",
        module_key="portal",
        display_name="Portal Gönderisi Detayı",
        description="Tek bir portal gönderisini, kullanıcının görme yetkisi varsa döndürür (aksi halde None).",
        intent_tags=("portal", "post", "detail", "record"),
        operation_type="READ_RECORD",
        read_or_write="read",
        permission_key="portal_feed",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.portal_read_post_detail",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Portal Gönderisi",
        evidence=(
            "app/models/portal_models.py:57 PortalPost; visibility reused from "
            "app/services/portal_service.py:220 can_user_view_post(user, post)"
        ),
    ),
    AssistantCapabilityEntry(
        capability_key="portal_list_flagged_posts_for_moderation",
        module_key="portal",
        display_name="Moderasyon Bekleyen Şikayetler",
        description="status='open' olan portal gönderi şikayetlerini (report) en yeni tarihe göre sınırlı sayıda listeler.",
        intent_tags=("portal", "moderation", "report", "flag"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="portal_moderation",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.portal_list_flagged_posts_for_moderation",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Portal Şikayet Kaydı",
        supports_pagination=True,
        evidence="app/models/portal_models.py:193 PortalPostReport.status; permission_key real menu_key at app/menu_registry_data_sections.py:136",
    ),

    # ------------------------------------------------------------------
    # file_center (auth_override exception -- see module docstring)
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="file_center_read_quota_status",
        module_key="file_center",
        display_name="Dosya Merkezi Kota Durumu",
        description="Aktif genel kota politikasını ve tüm kullanıcılar için toplam kullanılan depolama/dosya sayısını (agrega) döndürür.",
        intent_tags=("file_center", "quota", "storage", "policy"),
        operation_type="READ_RECORD",
        read_or_write="read",
        permission_key=None,
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.file_center_read_quota_status",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Dosya Merkezi Kota Politikası",
        evidence=(
            "app/models/file_center_models.py:194 FileQuotaUsage, :231 FileQuotaPolicy; "
            "gated by app/file_center/permissions.py:399 can_manage_file_center_settings, "
            "documented exception per app/services/settings/module_registry.py:147"
        ),
        extra={"auth_override": "app.file_center.permissions.can_manage_file_center_settings"},
    ),
    AssistantCapabilityEntry(
        capability_key="file_center_list_recent_security_scans",
        module_key="file_center",
        display_name="Son Dosya Güvenlik Taramaları",
        description="En son yapılan dosya güvenlik taramalarını (durum, tarayıcı, sonuç) sınırlı sayıda listeler.",
        intent_tags=("file_center", "security", "scan", "audit"),
        operation_type="LIST",
        read_or_write="read",
        permission_key=None,
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.file_center_list_recent_security_scans",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Dosya Güvenlik Tarama Kaydı",
        supports_pagination=True,
        evidence="app/models/file_center_models.py:205 FileSecurityScan; same auth_override exception as above",
        extra={"auth_override": "app.file_center.permissions.can_manage_file_center_settings"},
    ),
    AssistantCapabilityEntry(
        capability_key="file_center_explain_role_matrix",
        module_key="file_center",
        display_name="Dosya Merkezi Rol Matrisi Açıklaması",
        description="Aktif dosya merkezi rol izin satırlarını (yükleme, indirme, paylaşım linki, yönetim yetkileri) özetler.",
        intent_tags=("file_center", "role", "matrix", "permissions"),
        operation_type="EXPLAIN",
        read_or_write="read",
        permission_key=None,
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.file_center_explain_role_matrix",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Dosya Merkezi Rol Matrisi",
        evidence="app/models/file_center_models.py:306 FileCenterRolePermission.is_active; same auth_override exception as above",
        extra={"auth_override": "app.file_center.permissions.can_manage_file_center_settings"},
    ),

    # ------------------------------------------------------------------
    # communication
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="communication_list_active_announcements",
        module_key="communication",
        display_name="Aktif Duyurular",
        description="is_active=True olan duyuruları, en güncel yayın başlangıcına göre sınırlı sayıda listeler.",
        intent_tags=("communication", "announcement", "duyuru", "list"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="announcements",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.communication_list_active_announcements",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Duyuru Kaydı",
        supports_pagination=True,
        evidence="app/models/announcement_popup_models.py:18 Announcement.is_active; permission_key real menu_key at app/menu_registry_data_sections.py:683",
    ),
    AssistantCapabilityEntry(
        capability_key="communication_summarize_my_unread_messages",
        module_key="communication",
        display_name="Okunmamış Mesaj Özetim",
        description="Kullanıcının katılımcı olduğu mesaj konularından, son okunma zamanından sonra yeni mesajı olanların sayısını döndürür (kendi kapsamı).",
        intent_tags=("communication", "messages", "unread", "self"),
        operation_type="SUMMARIZE",
        read_or_write="read",
        permission_key="messages",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.communication_summarize_my_unread_messages",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Mesaj Konusu Katılımcı Kaydı",
        evidence="app/models/communication_models.py:232 MessageThread, :263 MessageThreadParticipant.last_read_at; permission_key real menu_key at app/menu_registry_data_sections.py:589",
    ),
    AssistantCapabilityEntry(
        capability_key="communication_read_announcement_detail",
        module_key="communication",
        display_name="Duyuru Detayı",
        description="Tek bir duyurunun başlığını, içeriğini ve yayın aralığını döndürür.",
        intent_tags=("communication", "announcement", "detail", "record"),
        operation_type="READ_RECORD",
        read_or_write="read",
        permission_key="announcements",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.communication_read_announcement_detail",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Duyuru Kaydı",
        evidence="app/models/announcement_popup_models.py:18 Announcement",
    ),

    # ------------------------------------------------------------------
    # surveys
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="surveys_list_my_assigned_surveys",
        module_key="surveys",
        display_name="Bana Atanmış Anketler",
        description="Kullanıcıya atanmış, yayınlanmış anketleri durum bilgisiyle (yanıtlandı/bekliyor) listeler (kendi kapsamı).",
        intent_tags=("surveys", "assigned", "self", "list"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="surveys",
        is_self_describing=False,
        service_handler="app.services.surveys.listing.get_assigned_surveys_for_user",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Anket Atama Kaydı",
        supports_pagination=False,
        evidence="REUSED existing function: app/services/surveys/listing.py:120 get_assigned_surveys_for_user(user)",
    ),
    AssistantCapabilityEntry(
        capability_key="surveys_list_active_surveys_for_management",
        module_key="surveys",
        display_name="Yönetim İçin Yayınlanmış Anketler",
        description="status='published' olan anketleri, oluşturulma tarihine göre sınırlı sayıda listeler.",
        intent_tags=("surveys", "management", "published", "list"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="survey_manage",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.surveys_list_active_surveys_for_management",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Anket Kaydı",
        supports_pagination=True,
        evidence="app/models/communication_models.py:431 Survey.status; permission_key real menu_key at app/menu_registry_data_sections.py:665",
    ),
    AssistantCapabilityEntry(
        capability_key="surveys_summarize_survey_results",
        module_key="surveys",
        display_name="Anket Sonuç Eğilimi",
        description="Bir anketin tamamlanma eğilimini (zaman içindeki yanıt sayısı) özetler.",
        intent_tags=("surveys", "results", "trend", "summary"),
        operation_type="SUMMARIZE",
        read_or_write="read",
        permission_key="survey_results",
        is_self_describing=False,
        service_handler="app.services.surveys.results.simple_completion_trend",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Anket Yanıt Kaydı",
        evidence="REUSED existing function: app/services/surveys/results.py:81 simple_completion_trend(survey_id)",
    ),

    # ------------------------------------------------------------------
    # support_help
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="support_help_list_my_tickets",
        module_key="support_help",
        display_name="Taleplerim",
        description="Kullanıcının kendi açtığı destek taleplerini, en güncel tarihe göre sınırlı sayıda listeler (kendi kapsamı).",
        intent_tags=("support", "tickets", "self", "list"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="support_my_tickets",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.support_help_list_my_tickets",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Destek Talebi Kaydı",
        supports_pagination=True,
        evidence="app/models/support_models.py:25 SupportTicket.created_by_user_id; permission_key real menu_key at app/menu_registry_data_sections.py:58",
    ),
    AssistantCapabilityEntry(
        capability_key="support_help_read_ticket_detail",
        module_key="support_help",
        display_name="Destek Talebi Detayı",
        description="Tek bir destek talebini, kullanıcı talebin sahibi veya atanan kişiyse döndürür (aksi halde None).",
        intent_tags=("support", "ticket", "detail", "record"),
        operation_type="READ_RECORD",
        read_or_write="read",
        permission_key="support_my_tickets",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.support_help_read_ticket_detail",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Destek Talebi Kaydı",
        evidence="app/models/support_models.py:25 SupportTicket (created_by_user_id / assigned_to_user_id scoping)",
    ),
    AssistantCapabilityEntry(
        capability_key="support_help_search_help_center_articles",
        module_key="support_help",
        display_name="Yardım Merkezi Makale Arama",
        description="Yayınlanmış yardım merkezi makalelerinde başlık/özet üzerinden basit metin araması yapar.",
        intent_tags=("support", "help_center", "search", "article"),
        operation_type="SEARCH",
        read_or_write="read",
        permission_key="support_help_admin",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.support_help_search_help_center_articles",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Yardım Merkezi Makalesi",
        supports_filters=True,
        supports_pagination=True,
        evidence=(
            "app/models/support_models.py:206 SupportHelpArticle.is_published; "
            "no dedicated general-browse menu_key exists yet for the help center itself, "
            "so this uses the closest real, existing key tied to that content area: "
            "'support_help_admin' (app/menu_registry.py:689, 'Rehber Yönetimi') -- "
            "flagged honestly rather than invented, see final report"
        ),
    ),

    # ------------------------------------------------------------------
    # ai_decision_support
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="ai_decision_support_list_open_recommendations",
        module_key="ai_decision_support",
        display_name="Açık AI Önerileri",
        description="status='open' olan AI önerilerini önem derecesine göre sınırlı sayıda listeler.",
        intent_tags=("ai", "recommendations", "open", "list"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="ai_center",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.ai_decision_support_list_open_recommendations",
        sensitivity="critical",
        audit_required=True,
        source_attribution_label="AI Öneri Kaydı",
        supports_pagination=True,
        evidence="app/models/ai_models.py:41 AIRecommendation.status; permission_key real menu_key at app/menu_registry_data_sections.py:733",
    ),
    AssistantCapabilityEntry(
        capability_key="ai_decision_support_summarize_usage",
        module_key="ai_decision_support",
        display_name="AI Kullanım Özeti",
        description="Son dönemdeki AI isteklerini sağlayıcı (provider) ve durum bazında gruplayıp sayar.",
        intent_tags=("ai", "usage", "summary", "provider"),
        operation_type="SUMMARIZE",
        read_or_write="read",
        permission_key="ai_center",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.ai_decision_support_summarize_usage",
        sensitivity="critical",
        audit_required=True,
        source_attribution_label="AI İstek Günlüğü",
        evidence="app/models/ai_models.py:7 AIRequestLog",
    ),
    AssistantCapabilityEntry(
        capability_key="ai_decision_support_explain_governance_settings",
        module_key="ai_decision_support",
        display_name="AI Governance Ayarları Açıklaması",
        description="Mevcut AI governance ayarlarını (eşik değerleri, haftalık özet ayarları) döndürür.",
        intent_tags=("ai", "governance", "settings", "explain"),
        operation_type="EXPLAIN",
        read_or_write="read",
        permission_key="ai_center",
        is_self_describing=False,
        service_handler="app.services.ai.governance_settings.get_ai_governance_settings",
        sensitivity="critical",
        audit_required=True,
        source_attribution_label="AI Governance Ayarı",
        evidence="REUSED existing function: app/services/ai/governance_settings.py:39 get_ai_governance_settings()",
    ),

    # ------------------------------------------------------------------
    # virtual_assistant
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="virtual_assistant_discover_available_modules",
        module_key="virtual_assistant",
        display_name="Kullanılabilir Modülleri Keşfet",
        description="Sistemdeki aktif modülleri (module_registry) ve bu kullanıcı için görünür olup olmadıklarını listeler.",
        intent_tags=("assistant", "discover", "modules", "self_describing"),
        operation_type="DISCOVER",
        read_or_write="read",
        permission_key=None,
        is_self_describing=True,
        service_handler=f"{_ADAPTERS}.virtual_assistant_discover_available_modules",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="BYS360 Modül Kataloğu",
        evidence="app/services/settings/module_registry.py:349 list_active_modules(); login-only, not menu-gated (describes access, does not grant it)",
    ),
    AssistantCapabilityEntry(
        capability_key="virtual_assistant_discover_my_capabilities",
        module_key="virtual_assistant",
        display_name="Kendi Yeteneklerimi Keşfet",
        description="Bu asistan kayıt defterindeki (capability registry) yetenekleri, mevcut kullanıcı için erişilebilir olup olmadıklarıyla birlikte listeler.",
        intent_tags=("assistant", "discover", "capabilities", "self_describing"),
        operation_type="DISCOVER",
        read_or_write="read",
        permission_key=None,
        is_self_describing=True,
        service_handler=f"{_ADAPTERS}.virtual_assistant_discover_my_capabilities",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="BYS360 Yetenek Kataloğu",
        evidence="self-referential over this same ASSISTANT_CAPABILITY_REGISTRY; login-only, not menu-gated",
    ),
    AssistantCapabilityEntry(
        capability_key="virtual_assistant_explain_role_matrix",
        module_key="virtual_assistant",
        display_name="Asistan Rol Matrisi Açıklaması",
        description="Sanal asistan modülünün rol bazlı görünürlük matrisini açıklar.",
        intent_tags=("assistant", "role_matrix", "explain"),
        operation_type="EXPLAIN",
        read_or_write="read",
        permission_key="ai_agent_panel",
        is_self_describing=False,
        service_handler="app.services.assistant_role_matrix_service.build_assistant_role_matrix",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Asistan Rol Matrisi",
        evidence=(
            "REUSED existing function: app/services/assistant_role_matrix_service.py:86 "
            "build_assistant_role_matrix(); permission_key real menu_key at app/menu_registry.py:873"
        ),
    ),
    AssistantCapabilityEntry(
        capability_key="virtual_assistant_search_knowledge_bank",
        module_key="virtual_assistant",
        display_name="BYS360 Bilgi Bankası Araması",
        description="Yöneticiler tarafından öğretilen, onaylı BYS360 bilgi bankası kayıtları arasında soruya en uygun cevabı arar.",
        intent_tags=("knowledge", "bilgi", "bankasi", "ogret", "faq", "soru", "cevap"),
        operation_type="SEARCH",
        read_or_write="read",
        permission_key="ai_agent_panel",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.virtual_assistant_search_knowledge_bank",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="BYS360 Bilgi Bankası",
        supports_filters=False,
        supports_pagination=False,
        evidence=(
            "REUSED existing function: app/services/ai_agent/knowledge.py:184 search_knowledge_answer() -- "
            "already filters to list_knowledge_entries(include_inactive=False) only (Phase B: inactive/"
            "unapproved entries never returned), already bounded (limit=3). permission_key='ai_agent_panel' "
            "matches the legacy build_knowledge_reply()'s actual audience (any authenticated user who can "
            "reach the assistant panel, not admin-only -- admin-only is can_manage_ai_knowledge(), which "
            "gates EDITING at app/ai_agent/routes.py's /knowledge routes, a separate concern from reading)."
        ),
        extra={"question_kwarg": "question"},
    ),

    # ------------------------------------------------------------------
    # dashboard
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="dashboard_summarize_my_home_context",
        module_key="dashboard",
        display_name="Ana Panel Özetim",
        description="Kullanıcının ana panel (home) özet bağlamını döndürür (kendi kapsamı).",
        intent_tags=("dashboard", "home", "summary", "self"),
        operation_type="SUMMARIZE",
        read_or_write="read",
        permission_key="dashboard",
        is_self_describing=False,
        service_handler="app.services.home_dashboard_service.build_home_summary_context",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Ana Panel Özeti",
        evidence="REUSED existing function: app/services/home_dashboard_service.py:220 build_home_summary_context(user)",
    ),
    AssistantCapabilityEntry(
        capability_key="dashboard_aggregate_my_home_page_panels",
        module_key="dashboard",
        display_name="Ana Panel Widget Toplamı",
        description="Kullanıcının ana panel sayfasındaki tüm widget/panel verilerini tek seferde toplar (kendi kapsamı).",
        intent_tags=("dashboard", "home", "widgets", "aggregate"),
        operation_type="AGGREGATE",
        read_or_write="read",
        permission_key="dashboard",
        is_self_describing=False,
        service_handler="app.services.home_dashboard_service.build_home_page_context",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Ana Panel Bağlamı",
        evidence="REUSED existing function: app/services/home_dashboard_service.py:122 build_home_page_context(user)",
    ),
    AssistantCapabilityEntry(
        capability_key="dashboard_explain_module",
        module_key="dashboard",
        display_name="Dashboard Modülü Açıklaması",
        description="Dashboard modülünün amacını ve widget görünürlüğünün şu an nasıl yönetildiğini (kod içinde role göre sabit) açıklar.",
        intent_tags=("dashboard", "explain", "module"),
        operation_type="EXPLAIN",
        read_or_write="read",
        permission_key="dashboard",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.dashboard_explain_module",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="BYS360 Modül Kataloğu",
        evidence=(
            "app/services/settings/module_registry.py get_module('dashboard'); "
            "widget-visibility-is-hardcoded fact confirmed at app/settings_center/routes.py:294"
        ),
    ),

    # ------------------------------------------------------------------
    # settings_auth
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="settings_auth_list_role_menu_defaults",
        module_key="settings_auth",
        display_name="Rol Menü Varsayılanları",
        description="Belirli bir rol için canlı (live) menü anahtarlarının varsayılan görünürlük durumunu döndürür.",
        intent_tags=("settings", "role", "menu", "defaults"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="settings",
        is_self_describing=False,
        service_handler="app.services.settings.menu_permissions.snapshot_role_menu_state",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Rol Menü Varsayılanı",
        evidence=(
            "REUSED existing function: app/services/settings/menu_permissions.py:60 "
            "snapshot_role_menu_state(role_name, all_menu_keys) -- caller supplies "
            "all_menu_keys (e.g. via filter_live_menu_keys(None))"
        ),
    ),
    AssistantCapabilityEntry(
        capability_key="settings_auth_list_unit_menu_overrides",
        module_key="settings_auth",
        display_name="Birim Menü Geçersiz Kılmaları",
        description="Belirli bir organizasyon birimi için tanımlı menü görünürlük geçersiz kılmalarını (override) listeler.",
        intent_tags=("settings", "unit", "menu", "override"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="settings",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.settings_auth_list_unit_menu_overrides",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Birim Menü Profili Kaydı",
        supports_pagination=True,
        evidence="app/models/settings_models.py:70 UnitMenuProfile",
    ),
    AssistantCapabilityEntry(
        capability_key="settings_auth_summarize_role_permission_coverage",
        module_key="settings_auth",
        display_name="Rol İzin Kapsama Özeti",
        description="Her rol için kaç adet açık RoleMenuDefault kaydı bulunduğunu sayar (rol bazlı kapsama özeti).",
        intent_tags=("settings", "role", "coverage", "summary"),
        operation_type="SUMMARIZE",
        read_or_write="read",
        permission_key="settings",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.settings_auth_summarize_role_permission_coverage",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Rol Menü Varsayılanı",
        evidence="app/models/settings_models.py:13 RoleMenuDefault -- GROUP BY role_name, bounded by the small, fixed set of real roles",
    ),

    # ------------------------------------------------------------------
    # notifications
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="notifications_list_my_notifications",
        module_key="notifications",
        display_name="Bildirimlerim",
        description="Kullanıcının kendi bildirimlerini, en güncel tarihe göre sınırlı sayıda listeler (kendi kapsamı).",
        intent_tags=("notifications", "self", "list"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="notifications",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.notifications_list_my_notifications",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Bildirim Kaydı",
        supports_pagination=True,
        evidence="app/models/communication_models.py:408 Notification.user_id; permission_key real menu_key at app/menu_registry_data_sections.py:84",
    ),
    AssistantCapabilityEntry(
        capability_key="notifications_summarize_my_unread_count",
        module_key="notifications",
        display_name="Okunmamış Bildirim Sayım",
        description="Kullanıcının okunmamış bildirim sayısını, öncelik (priority) bazında gruplayarak döndürür (kendi kapsamı).",
        intent_tags=("notifications", "unread", "self", "summary"),
        operation_type="SUMMARIZE",
        read_or_write="read",
        permission_key="notifications",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.notifications_summarize_my_unread_count",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Bildirim Kaydı",
        evidence="app/models/communication_models.py:408 Notification.is_read",
    ),
    AssistantCapabilityEntry(
        capability_key="notifications_read_notification_detail",
        module_key="notifications",
        display_name="Bildirim Detayı",
        description="Kullanıcıya ait tek bir bildirimin tam içeriğini döndürür (kendi kapsamı).",
        intent_tags=("notifications", "detail", "self", "record"),
        operation_type="READ_RECORD",
        read_or_write="read",
        permission_key="notifications",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.notifications_read_notification_detail",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Bildirim Kaydı",
        evidence="app/models/communication_models.py:408 Notification, scoped to user_id",
    ),

    # ------------------------------------------------------------------
    # email_automation
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="email_automation_summarize_performance_reminder_health",
        module_key="email_automation",
        display_name="Performans Hatırlatma E-postası Sağlık Özeti",
        description="Son dönemdeki performans hatırlatma/sonuç e-postalarının başarı/hata sayısını özetler.",
        intent_tags=("email", "performance", "reminder", "health"),
        operation_type="SUMMARIZE",
        read_or_write="read",
        permission_key=None,
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.email_automation_summarize_performance_reminder_health",
        sensitivity="internal",
        audit_required=True,
        source_attribution_label="Performans E-postası Günlüğü",
        evidence=(
            "app/models/communication_models.py:114 MailLog; mail_type constants "
            "from app/services/mail_core.py:30 PERFORMANCE_REMINDER_MAIL_TYPE / :31 PERFORMANCE_RESULT_MAIL_TYPE; "
            "enforced via app.route_support.ADMIN_FAMILY_ROLES, not a menu_key"
        ),
        extra={"auth_override": "admin_required_role_family"},
    ),
    AssistantCapabilityEntry(
        capability_key="email_automation_explain_daily_weather_mail_settings",
        module_key="email_automation",
        display_name="Günlük Bilgilendirme E-postası Ayarları Açıklaması",
        description="Günlük bilgilendirme e-postasının mevcut yapılandırmasını (aktiflik, gönderim saati, kapsam) döndürür.",
        intent_tags=("email", "daily_weather_mail", "settings", "explain"),
        operation_type="EXPLAIN",
        read_or_write="read",
        permission_key=None,
        is_self_describing=False,
        service_handler="app.services.daily_weather_mail.current_config",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Günlük Bilgilendirme E-postası Ayarı",
        evidence=(
            "REUSED existing function: app/services/daily_weather_mail.py:297 current_config(). "
            "permission_key was originally 'daily_weather_mail' (real menu_key declared at "
            "app/menu_registry_data_sections.py:825, with correct role defaults in "
            "app/menu_registry.py:1345-1348) -- Phase J's mechanical success-path matrix caught "
            "admin being denied it. Root cause: 'daily_weather_mail' is missing from "
            "app.live_scope.LIVE_SETTINGS_MENU_KEYS, the exact same class of bug already found "
            "and fixed for 'executive_summary'/'reports' in the prior orphan-auth-key closure "
            "wave -- but fixing app/live_scope.py again here would expand this wave's scope into "
            "an unrelated pre-existing gap. Switched instead to the same admin_required_role_family "
            "auth_override this file's own sibling capability "
            "(email_automation_summarize_performance_reminder_health) already uses -- a real, "
            "already-enforced, already-tested boundary, not a new one."
        ),
        extra={"auth_override": "admin_required_role_family"},
    ),
    AssistantCapabilityEntry(
        capability_key="email_automation_list_recent_mail_log",
        module_key="email_automation",
        display_name="Son Günlük Bilgilendirme E-postaları",
        description="Gönderilen son günlük bilgilendirme e-postası kayıtlarını sınırlı sayıda listeler.",
        intent_tags=("email", "daily_weather_mail", "log", "list"),
        operation_type="LIST",
        read_or_write="read",
        permission_key=None,
        is_self_describing=False,
        service_handler="app.services.daily_weather_mail.get_recent_logs",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="E-posta Gönderim Günlüğü",
        supports_pagination=True,
        evidence=(
            "REUSED existing function: app/services/daily_weather_mail.py:569 "
            "get_recent_logs(limit=20) -- already clamps its own limit to [1, 100]. Same "
            "'daily_weather_mail' live-scope gap and same admin_required_role_family fix as "
            "email_automation_explain_daily_weather_mail_settings above -- see that entry's "
            "evidence for the full explanation."
        ),
        extra={"auth_override": "admin_required_role_family"},
    ),

    # ------------------------------------------------------------------
    # scheduled_jobs
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="scheduled_jobs_read_feedback_followup_status",
        module_key="scheduled_jobs",
        display_name="Geri Bildirim Takip Zamanlayıcısı Durumu",
        description="Geri bildirim takip zamanlayıcısının ortam değişkeni bazlı etkinlik durumunu döndürür.",
        intent_tags=("scheduled_jobs", "scheduler", "status"),
        operation_type="READ_RECORD",
        read_or_write="read",
        permission_key="settings_center_scheduled_jobs",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.scheduled_jobs_read_feedback_followup_status",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Zamanlanmış İş Durumu",
        evidence=(
            "app/services/performance/feedback_followup_scheduler.py:39 "
            "init_feedback_followup_scheduler, env BYS360_FEEDBACK_FOLLOWUP_SCHEDULER; "
            "permission_key real menu_key at app/menu_registry_data_sections.py:1106"
        ),
    ),
    AssistantCapabilityEntry(
        capability_key="scheduled_jobs_list_recent_digest_jobs",
        module_key="scheduled_jobs",
        display_name="Son Özet (Digest) İşleri",
        description="En son çalışan/kuyruğa alınan bildirim özet (digest) işlerini sınırlı sayıda listeler.",
        intent_tags=("scheduled_jobs", "digest", "list"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="settings_center_scheduled_jobs",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.scheduled_jobs_list_recent_digest_jobs",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Bildirim Özet İşi Kaydı",
        supports_pagination=True,
        evidence="app/models/communication_phase5_models.py:42 CommunicationDigestJob",
    ),
    AssistantCapabilityEntry(
        capability_key="scheduled_jobs_summarize_automation_health",
        module_key="scheduled_jobs",
        display_name="Otomasyon Sağlık Özeti",
        description="Son iletişim otomasyonu günlüklerini durum (status) bazında gruplayıp sayar.",
        intent_tags=("scheduled_jobs", "automation", "health", "summary"),
        operation_type="SUMMARIZE",
        read_or_write="read",
        permission_key="settings_center_scheduled_jobs",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.scheduled_jobs_summarize_automation_health",
        sensitivity="internal",
        audit_required=False,
        source_attribution_label="Otomasyon Günlüğü",
        evidence="app/models/communication_phase5_models.py:110 CommunicationAutomationLog.status",
    ),

    # ------------------------------------------------------------------
    # security_session
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="security_session_read_captcha_policy",
        module_key="security_session",
        display_name="CAPTCHA Politikası",
        description="Mevcut CAPTCHA etkinlik ve zorunluluk ayarlarını (ortam değişkeni bazlı) döndürür.",
        intent_tags=("security", "captcha", "policy"),
        operation_type="READ_RECORD",
        read_or_write="read",
        permission_key="settings_center_security",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.security_session_read_captcha_policy",
        sensitivity="critical",
        audit_required=True,
        source_attribution_label="Güvenlik Yapılandırması",
        evidence=(
            "app/security/captcha_guard.py:64 is_captcha_required, config CAPTCHA_ENABLED; "
            "config.py:640 LOGIN_FORCE_CAPTCHA_FOR_UNKNOWN_USER; "
            "permission_key real menu_key at app/menu_registry_data_sections.py:1115"
        ),
    ),
    # security_session is deliberately capped at exactly ONE capability
    # (coordinator decision, not this implementer's discretion): the module
    # is `system_critical`/`security_level=critical` in MODULE_REGISTRY and
    # has no route_endpoint at all. A prior research pass on this same
    # project explicitly warned that even seemingly-safe aggregation here
    # (e.g. "how many CAPTCHA failures today", or listing which accounts are
    # currently locked out) could assist an attacker in probing lockout
    # thresholds or performing account-enumeration reconnaissance -- so no
    # LIST/SEARCH/AGGREGATE capability is registered for this module, only
    # the one boolean-policy EXPLAIN below. Do not add more here without a
    # separate, explicit security review.

    # ------------------------------------------------------------------
    # audit
    # ------------------------------------------------------------------
    AssistantCapabilityEntry(
        capability_key="audit_list_recent_change_logs",
        module_key="audit",
        display_name="Son Ayar Değişiklik Kayıtları",
        description="En son ayar değişiklik günlüğü kayıtlarını sınırlı sayıda listeler.",
        intent_tags=("audit", "change_log", "list"),
        operation_type="LIST",
        read_or_write="read",
        permission_key="settings",
        is_self_describing=False,
        service_handler="app.services.settings.change_logs.list_recent_settings_change_logs",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Ayar Değişiklik Günlüğü",
        supports_pagination=True,
        evidence=(
            "REUSED existing function: app/services/settings/change_logs.py:80 "
            "list_recent_settings_change_logs(limit=12, target_user_id=None) -- already bounded and already "
            "wraps its own query in try/except with rollback"
        ),
    ),
    AssistantCapabilityEntry(
        capability_key="audit_read_change_log_detail",
        module_key="audit",
        display_name="Ayar Değişiklik Kaydı Detayı",
        description="Tek bir ayar değişiklik günlüğü kaydının tam içeriğini (önceki/yeni durum) döndürür.",
        intent_tags=("audit", "change_log", "detail", "record"),
        operation_type="READ_RECORD",
        read_or_write="read",
        permission_key="settings",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.audit_read_change_log_detail",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Ayar Değişiklik Günlüğü",
        evidence="app/models/settings_models.py:89 SettingsChangeLog",
    ),
    AssistantCapabilityEntry(
        capability_key="audit_summarize_recent_change_activity",
        module_key="audit",
        display_name="Son Değişiklik Aktivitesi Özeti",
        description="Son ayar değişiklik kayıtlarını kapsam (change_scope) bazında gruplayıp sayar.",
        intent_tags=("audit", "change_log", "summary", "activity"),
        operation_type="SUMMARIZE",
        read_or_write="read",
        permission_key="settings",
        is_self_describing=False,
        service_handler=f"{_ADAPTERS}.audit_summarize_recent_change_activity",
        sensitivity="sensitive",
        audit_required=True,
        source_attribution_label="Ayar Değişiklik Günlüğü",
        evidence="app/models/settings_models.py:89 SettingsChangeLog.change_scope -- bounded to the most recent N rows before grouping",
    ),
]


def get_capability_registry() -> list[AssistantCapabilityEntry]:
    return list(ASSISTANT_CAPABILITY_REGISTRY)


def get_capability(capability_key: str) -> AssistantCapabilityEntry | None:
    for entry in ASSISTANT_CAPABILITY_REGISTRY:
        if entry.capability_key == capability_key:
            return entry
    return None


def list_capabilities_for_module(module_key: str) -> list[AssistantCapabilityEntry]:
    return [entry for entry in ASSISTANT_CAPABILITY_REGISTRY if entry.module_key == module_key]


def list_active_capabilities() -> list[AssistantCapabilityEntry]:
    return [entry for entry in ASSISTANT_CAPABILITY_REGISTRY if entry.active]


def find_duplicate_capability_keys() -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for entry in ASSISTANT_CAPABILITY_REGISTRY:
        if entry.capability_key in seen:
            duplicates.append(entry.capability_key)
        seen.add(entry.capability_key)
    return duplicates


def find_capabilities_missing_permission() -> list[str]:
    """Capabilities with no real authorization path at all.

    A capability is considered properly gated if it has a real
    `permission_key`, OR is explicitly `is_self_describing=True`, OR
    documents a reviewed `extra["auth_override"]` (the three documented
    exceptions -- see module docstring). Anything else is a gap."""
    missing: list[str] = []
    for entry in ASSISTANT_CAPABILITY_REGISTRY:
        if entry.permission_key:
            continue
        if entry.is_self_describing:
            continue
        if entry.extra.get("auth_override"):
            continue
        missing.append(entry.capability_key)
    return missing


def find_capabilities_with_orphan_module_key() -> list[str]:
    """Capabilities whose module_key does not exist in the real,
    independently-maintained MODULE_REGISTRY."""
    known_module_keys = {entry.module_key for entry in MODULE_REGISTRY}
    return [
        entry.capability_key
        for entry in ASSISTANT_CAPABILITY_REGISTRY
        if entry.module_key not in known_module_keys
    ]


def find_capabilities_with_unresolvable_service() -> list[str]:
    """Capabilities whose service_handler dotted path does not actually
    import to a real, callable function in this worktree."""
    unresolvable: list[str] = []
    for entry in ASSISTANT_CAPABILITY_REGISTRY:
        handler = entry.service_handler or ""
        if "." not in handler:
            unresolvable.append(entry.capability_key)
            continue
        module_path, _, attr_name = handler.rpartition(".")
        try:
            module = importlib.import_module(module_path)
            target = getattr(module, attr_name)
        except Exception:
            logger.exception(
                "assistant_v2 capability_registry: unresolvable service_handler %r for capability %r",
                handler,
                entry.capability_key,
            )
            unresolvable.append(entry.capability_key)
            continue
        if not callable(target):
            unresolvable.append(entry.capability_key)
    return unresolvable


def find_capabilities_with_invalid_operation_type() -> list[str]:
    return [
        entry.capability_key
        for entry in ASSISTANT_CAPABILITY_REGISTRY
        if entry.operation_type not in OPERATION_TYPES
    ]


__all__ = [
    "AssistantCapabilityEntry",
    "ASSISTANT_CAPABILITY_REGISTRY",
    "OPERATION_TYPES",
    "READ_WRITE_VALUES",
    "SENSITIVITY_LEVELS",
    "get_capability_registry",
    "get_capability",
    "list_capabilities_for_module",
    "list_active_capabilities",
    "find_duplicate_capability_keys",
    "find_capabilities_missing_permission",
    "find_capabilities_with_orphan_module_key",
    "find_capabilities_with_unresolvable_service",
    "find_capabilities_with_invalid_operation_type",
]
