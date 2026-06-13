from __future__ import annotations



from app.core.datetime_utils import utc_now
from datetime import datetime
import io
import json
import re

from flask import flash, redirect, request, send_file, url_for
from flask_login import current_user

from app.extensions import db
from app.menu_registry import (
    flatten_menu_definitions as flatten_settings_menu_definitions,
    get_grouped_menu_definitions,
)
from app.main_handlers.constants import SECURITY_QUESTION_CHOICES
from app.models import SystemSetting, User, UserMenuPermission
from app.route_support import safe_render
from app.services.profile_photo_service import (
    delete_profile_photo_file as _delete_profile_photo_file,
    save_profile_photo as _save_profile_photo,
)
from app.services.settings_service import (
    build_effective_user_menu_context,
    build_settings_foundation_context,
    build_settings_profile_context,
    build_settings_ui_diagnostics_panel,
    clear_user_menu_overrides,
    ensure_settings_phase1_seeded,
    get_role_default_menu_keys,
    get_unit_profile_menu_keys,
    save_module_settings_from_form,
    save_role_menu_defaults,
    save_system_settings_from_form,
    save_unit_menu_profile,
    save_user_menu_overrides,
    rollback_settings_change,
)
from app.view_helpers import enforce_first_login_security_flow_redirect
import logging
logger = logging.getLogger(__name__)


COMMUNICATION_POLICY_ROLE_OPTIONS = [
    ("admin", "Admin"),
    ("baskan", "Başkan"),
    ("baskan_yardimcisi", "Başkan Yardımcısı"),
    ("grup_baskani", "Grup Başkanı"),
    ("mali_musavir", "Mali Müşavir"),
    ("koordinator", "Koordinatör"),
    ("birim_sorumlusu", "Birim Sorumlusu"),
    ("personel", "Personel"),
]


def _build_communication_policy_items(grouped_menu_definitions, flat_menu_items):
    communication_items = list(grouped_menu_definitions.get("İletişim ve Anket Yönetimi", []) or [])
    existing_keys = {item["key"] for item in communication_items if isinstance(item, dict)}
    for item in flat_menu_items:
        key = item.get("key")
        if key == "notifications" and key not in existing_keys:
            communication_items.insert(1, item)
            existing_keys.add(key)
    return communication_items


def _build_communication_role_matrix(policy_items):
    policy_items = [item for item in (policy_items or []) if isinstance(item, dict) and item.get("key")]
    role_rows = []
    item_rows = []

    role_visibility = {}
    static_role_visibility = {}
    for role_key, role_label in COMMUNICATION_POLICY_ROLE_OPTIONS:
        visible_keys = set(get_role_default_menu_keys(role_key))
        static_keys = set(get_role_default_menu_keys(role_key, prefer_database=False))
        static_keys.update(get_assistant_role_matrix_recommended_keys(role_key))
        role_visibility[role_key] = visible_keys
        static_role_visibility[role_key] = static_keys
        role_rows.append({
            "role_key": role_key,
            "role_label": role_label,
            "visible_count": len([item for item in policy_items if item["key"] in visible_keys]),
            "recommended_count": len([item for item in policy_items if item["key"] in static_keys]),
        })

    for item in policy_items:
        states = []
        visible_count = 0
        recommended_roles = []
        for role_key, role_label in COMMUNICATION_POLICY_ROLE_OPTIONS:
            is_visible = item["key"] in role_visibility.get(role_key, set())
            is_recommended = item["key"] in static_role_visibility.get(role_key, set())
            if is_visible:
                visible_count += 1
            if is_recommended:
                recommended_roles.append(role_label)
            states.append({
                "role_key": role_key,
                "role_label": role_label,
                "is_visible": is_visible,
                "is_recommended": is_recommended,
            })
        item_rows.append({
            "key": item["key"],
            "label": item.get("label") or item["key"],
            "icon": item.get("icon") or "fa-solid fa-circle",
            "visible_count": visible_count,
            "states": states,
            "recommended_roles": recommended_roles,
        })

    return {
        "roles": role_rows,
        "rows": item_rows,
        "items": item_rows,
        "item_count": len(item_rows),
    }


# BYS360_SETTINGS_MODULE_ROLE_MATRIX_V12_BEGIN
# Ayarlar > Modül Bazlı Rol Matrisleri güncel canlı kapsam.
# Bu blok; Yardım Merkezi V2, Sanal Asistan V9 ve güncel Performans Yönetimi
# sekmelerinin rol bazlı yönetim satırlarını tek merkezde görünür yapar.
# Login, şifre, CAPTCHA, auth, DB bağlantısı veya gerçek endpoint yetki kontrollerine dokunmaz.

SUPPORT_HELP_ROLE_MATRIX_ITEMS = [
    {"key": "support_index", "label": "Yardım Merkezi", "icon": "fa-solid fa-circle-question"},
    {"key": "support_new", "label": "Yeni Talep Aç", "icon": "fa-solid fa-plus"},
    {"key": "support_my_tickets", "label": "Taleplerim", "icon": "fa-solid fa-folder-open"},
    {"key": "support_assigned", "label": "Bana Atananlar", "icon": "fa-solid fa-user-check"},
    {"key": "support_all", "label": "Tüm Talepler", "icon": "fa-solid fa-table-list"},
]

PERFORMANCE_ROLE_MATRIX_V12_ITEMS = [
    {"key": "performance_tasks", "label": "Görevlerim", "icon": "fa-solid fa-list-check"},
    {"key": "performance_scorecard", "label": "Not Karnesi", "icon": "fa-solid fa-id-card"},
    {"key": "my_performance_comparison", "label": "Personel Analizi", "icon": "fa-solid fa-chart-line"},
    {"key": "performance_reports", "label": "Performans Raporları", "icon": "fa-solid fa-chart-pie"},
    {"key": "performance_criteria", "label": "Değerlendirme Kriterleri", "icon": "fa-solid fa-list-ul"},
    {"key": "performance_periods", "label": "Dönemler ve Kapsamlar", "icon": "fa-solid fa-calendar-days"},
    {"key": "performance_evaluation_tasks", "label": "Değerlendirme Görevleri", "icon": "fa-solid fa-clipboard-check"},
    {"key": "performance_meeting_p3_reminders", "label": "Hatırlatma ve Aksatan Amirler", "icon": "fa-solid fa-bell"},
    {"key": "performance_interim_notes", "label": "Dönem İçi Notlar", "icon": "fa-regular fa-note-sticky"},
    {"key": "performance_development_guidance", "label": "Gelişim Rehberi", "icon": "fa-solid fa-seedling"},
    {"key": "performance_process_tracking", "label": "Süreç Takibi", "icon": "fa-solid fa-route"},
    {"key": "performance_process_reports", "label": "Süreç Raporları", "icon": "fa-solid fa-chart-line"},
    {"key": "performance_president_approvals", "label": "Başkan / Üst Onayları", "icon": "fa-solid fa-stamp"},
    {"key": "performance_personnel_support_publish_approval", "label": "Yayın Ön Onayı", "icon": "fa-solid fa-user-check"},
    {"key": "performance_archive", "label": "Geçmiş Karne Arşivi", "icon": "fa-solid fa-box-archive"},
    {"key": "performance_task_management", "label": "Görev Yönetimi", "icon": "fa-solid fa-screwdriver-wrench"},
    {"key": "performance_hierarchy_tree", "label": "Hiyerarşi Ağacı", "icon": "fa-solid fa-sitemap"},
    {"key": "performance_hierarchy_assignments", "label": "Hiyerarşi Atamaları ve Ayarları", "icon": "fa-solid fa-code-branch"},
    {"key": "performance_team_compare", "label": "Ekip / Personel Analizi", "icon": "fa-solid fa-people-arrows"},
    {"key": "performance_feedback_meetings", "label": "Gelişim Görüşmeleri", "icon": "fa-solid fa-calendar-week"},
    {"key": "team_performance_comparison_history", "label": "Personel Dönem Analizi", "icon": "fa-solid fa-code-compare"},
    {"key": "performance_publish", "label": "Yayın Yönetimi", "icon": "fa-solid fa-bullhorn"},
]

ASSISTANT_ROLE_MATRIX_ITEMS = [
    {"key": "assistant_center", "label": "Sanal Asistan Merkezi", "icon": "fa-solid fa-robot"},
    {"key": "assistant_quick_help", "label": "Hızlı Rehber Cevapları", "icon": "fa-solid fa-circle-question"},
    {"key": "assistant_my_summary", "label": "Benim Özetim Kartları", "icon": "fa-solid fa-gauge-high"},
    {"key": "assistant_support_routing", "label": "Yardım Merkezi Yönlendirmesi", "icon": "fa-solid fa-headset"},
    {"key": "assistant_performance_guidance", "label": "Performans Süreç Rehberi", "icon": "fa-solid fa-chart-line"},
    {"key": "assistant_president_approval_guidance", "label": "Başkan / Üst Onay Rehberi", "icon": "fa-solid fa-stamp"},
    {"key": "assistant_publish_preapproval_guidance", "label": "Yayın Ön Onayı Rehberi", "icon": "fa-solid fa-user-check"},
    {"key": "assistant_interim_notes_guidance", "label": "Dönem İçi Not Rehberi", "icon": "fa-regular fa-note-sticky"},
    {"key": "assistant_development_guidance", "label": "Gelişim Önerisi Rehberi", "icon": "fa-solid fa-seedling"},
    {"key": "assistant_archive_guidance", "label": "Geçmiş Karne Arşivi Rehberi", "icon": "fa-solid fa-box-archive"},
    {"key": "assistant_process_alerts", "label": "Süreç Hatırlatma ve Uyarılar", "icon": "fa-solid fa-triangle-exclamation"},
    {"key": "assistant_my_reminders", "label": "Bana Ait Hatırlatmalar", "icon": "fa-solid fa-bell"},
    {"key": "assistant_scheduled_tasks", "label": "Zamanlanmış İş Planlama", "icon": "fa-solid fa-calendar-check"},
    {"key": "assistant_report_generate", "label": "Rapor Oluşturma", "icon": "fa-solid fa-file-lines"},
    {"key": "assistant_report_share", "label": "Rapor Paylaşımı", "icon": "fa-solid fa-share-nodes"},
    {"key": "assistant_ai_summary", "label": "AI Özet ve Karar Notu", "icon": "fa-solid fa-brain"},
    {"key": "assistant_logs", "label": "Asistan İşlem Logları", "icon": "fa-solid fa-clipboard-list"},
    {"key": "assistant_settings", "label": "Asistan Ayarları", "icon": "fa-solid fa-sliders"},
]

ASSISTANT_ROLE_MATRIX_KEYS = {item["key"] for item in ASSISTANT_ROLE_MATRIX_ITEMS}

ASSISTANT_ROLE_MATRIX_RECOMMENDED = {
    "admin": set(ASSISTANT_ROLE_MATRIX_KEYS),
    "baskan": {
        "assistant_center", "assistant_quick_help", "assistant_my_summary", "assistant_support_routing",
        "assistant_performance_guidance", "assistant_president_approval_guidance",
        "assistant_publish_preapproval_guidance", "assistant_process_alerts", "assistant_report_generate",
        "assistant_report_share", "assistant_ai_summary", "assistant_logs",
    },
    "baskan_yardimcisi": {
        "assistant_center", "assistant_quick_help", "assistant_my_summary", "assistant_support_routing",
        "assistant_performance_guidance", "assistant_publish_preapproval_guidance", "assistant_interim_notes_guidance",
        "assistant_development_guidance", "assistant_process_alerts", "assistant_report_generate", "assistant_ai_summary",
    },
    "grup_baskani": {
        "assistant_center", "assistant_quick_help", "assistant_my_summary", "assistant_support_routing",
        "assistant_performance_guidance", "assistant_publish_preapproval_guidance", "assistant_interim_notes_guidance",
        "assistant_development_guidance", "assistant_archive_guidance", "assistant_process_alerts", "assistant_my_reminders",
    },
    "mali_musavir": {
        "assistant_center", "assistant_quick_help", "assistant_my_summary", "assistant_support_routing",
        "assistant_performance_guidance", "assistant_process_alerts", "assistant_report_generate", "assistant_ai_summary",
    },
    "koordinator": {
        "assistant_center", "assistant_quick_help", "assistant_my_summary", "assistant_support_routing",
        "assistant_performance_guidance", "assistant_interim_notes_guidance", "assistant_development_guidance",
        "assistant_archive_guidance", "assistant_process_alerts", "assistant_my_reminders",
    },
    "birim_sorumlusu": {
        "assistant_center", "assistant_quick_help", "assistant_my_summary", "assistant_support_routing",
        "assistant_performance_guidance", "assistant_interim_notes_guidance", "assistant_development_guidance",
        "assistant_process_alerts", "assistant_my_reminders",
    },
    "personel": {
        "assistant_center", "assistant_quick_help", "assistant_my_summary", "assistant_support_routing",
        "assistant_archive_guidance", "assistant_process_alerts", "assistant_my_reminders",
    },
}

ROLE_MATRIX_POLICY_CONFIGS = [
    {
        "key": "general",
        "section_id": "general-role-policy",
        "title": "Genel Rol Matrisi",
        "description": "Dashboard, görevler, bildirimler, not karnesi, personel analizi ve genel rapor sekmelerinin hangi rollerde açık olacağını yönetin. Yardım Merkezi ayrı kartta daha detaylı yönetilir.",
        "menu_groups": ["Genel"],
        "extra_keys": [],
        "badges": [
            ("fa-solid fa-house", "Dashboard ve bildirimler: temel erişim"),
            ("fa-solid fa-chart-line", "Personel analizi: yayın ve yetki sınırı"),
            ("fa-solid fa-shield-halved", "Rolsüz kullanıcı: güvenli kapalı"),
        ],
        "reset_text": "Genel rol politikasına dön",
    },
    {
        "key": "support_help",
        "section_id": "support-help-role-policy",
        "title": "Yardım Merkezi ve Destek Rol Matrisi",
        "description": "Yardım Merkezi V2, yeni talep açma, kişinin kendi talepleri, kendisine atanan talepler ve tüm talepler görünürlüğünü rol bazlı yönetin. Kişisel talep ekranları tüm kullanıcılara açık kalabilir; atama ve tüm talepler yönetici kapsamıyla sınırlıdır.",
        "menu_groups": [],
        "extra_keys": [],
        "synthetic_items": SUPPORT_HELP_ROLE_MATRIX_ITEMS,
        "badges": [
            ("fa-solid fa-circle-question", "Yardım merkezi: tüm kullanıcılar"),
            ("fa-solid fa-headset", "Talep yönetimi: yönetici kapsamı"),
            ("fa-solid fa-lock", "Talep içeriği: yetki sınırı"),
        ],
        "reset_text": "Yardım ve destek rol politikasına dön",
    },
    {
        "key": "personnel",
        "section_id": "personnel-role-policy",
        "title": "Personel Yönetimi Rol Matrisi",
        "description": "Personel listesi, birim-pozisyon yönetimi, özlük operasyonları, izin-devamsızlık ve personel raporları sekmelerinin rol bazlı görünürlüğünü yönetin. Standart personelde yönetim sekmeleri kapalı kalmalıdır.",
        "menu_groups": ["Personel Yönetimi"],
        "extra_keys": [],
        "badges": [
            ("fa-solid fa-users-gear", "Yönetim sekmeleri: yetkili roller"),
            ("fa-solid fa-user", "Personel: yönetim sekmesi kapalı"),
            ("fa-solid fa-shield-halved", "Rolsüz/özel durum: güvenli kapalı"),
        ],
        "reset_text": "Personel yönetimi rol politikasına dön",
    },
    {
        "key": "performance",
        "section_id": "performance-role-policy",
        "title": "Performans Yönetimi Rol Matrisi",
        "description": "Güncel performans omurgasındaki kriter, dönem/kapsam, değerlendirme görevleri, Başkan/Üst Onay, yayın ön onayı, süreç takibi, süreç raporları, dönem içi notlar, gelişim rehberi, geçmiş karne arşivi ve yayın sekmelerinin rol bazlı görünürlüğünü yönetin.",
        "menu_groups": [],
        "extra_keys": [],
        "synthetic_items": PERFORMANCE_ROLE_MATRIX_V12_ITEMS,
        "badges": [
            ("fa-solid fa-stamp", "Başkan/Üst Onay: Başkan ve Admin"),
            ("fa-solid fa-user-check", "Yayın ön onayı: Personel ve Destek kontrolü"),
            ("fa-solid fa-route", "Süreç takibi: yönetici kapsamı"),
        ],
        "reset_text": "Performans rol politikasına dön",
    },
    {
        "key": "communication",
        "section_id": "communication-role-policy",
        "title": "İletişim ve Anket Rol Matrisi",
        "description": "Mesajlar, bildirimler, duyurular, anketler, geri bildirim, nabız, kampanya, sonuç ve aksiyon ekranlarının hangi rollerde açık olduğunu yönetin.",
        "menu_groups": ["İletişim ve Anket Yönetimi"],
        "extra_keys": ["notifications"],
        "badges": [
            ("fa-solid fa-envelope", "Mesajlar: katılımcı/yetki bazlı"),
            ("fa-solid fa-square-poll-vertical", "Anketler: atama ve rol ayrımı"),
            ("fa-solid fa-chart-column", "Sonuçlar: yönetici kapsamı"),
        ],
        "reset_text": "İletişim ve anket rol politikasına dön",
    },
    {
        "key": "ai",
        "section_id": "ai-role-policy",
        "title": "AI Karar Destek Rol Matrisi",
        "description": "AI Karar Destek Merkezi, yönetici özeti, performans/personel/anket/geri bildirim/destek analizleri, redaksiyon kuralları ve işlem loglarının hangi rollerde açık olacağını yönetin. AI karar vermez; yalnızca yetkili rollere kontrollü özet ve analiz desteği sağlar.",
        "menu_groups": ["AI Karar Destek Merkezi"],
        "extra_keys": [],
        "badges": [
            ("fa-solid fa-brain", "AI: kontrollü karar destek"),
            ("fa-solid fa-user-shield", "Yetki sınırı aşılmaz"),
            ("fa-solid fa-file-shield", "Log ve redaksiyon ilkesi korunur"),
        ],
        "reset_text": "AI karar destek rol politikasına dön",
    },
    {
        "key": "assistant",
        "section_id": "assistant-role-policy",
        "title": "Sanal Asistan Rol Matrisi",
        "description": "Sanal Asistan V9 kapsamındaki hızlı rehber cevapları, güvenli özet kartları, Yardım Merkezi yönlendirmesi, performans süreç rehberi, Başkan/Üst Onay, yayın ön onayı, dönem içi not, gelişim önerisi, geçmiş karne arşivi, hatırlatma ve rapor yetkilerini yönetin.",
        "menu_groups": [],
        "extra_keys": [],
        "synthetic_items": ASSISTANT_ROLE_MATRIX_ITEMS,
        "badges": [
            ("fa-solid fa-robot", "Sanal Asistan: güvenli rehber"),
            ("fa-solid fa-gauge-high", "Benim özetim: hassas içerik yok"),
            ("fa-solid fa-route", "Yönlendirme: yetki sınırı"),
        ],
        "reset_text": "Sanal asistan rol politikasına dön",
    },
    {
        "key": "settings_security",
        "section_id": "settings-security-role-policy",
        "title": "Ayarlar ve Güvenlik Rol Matrisi",
        "description": "Hesabım, Ayarlar, DB Kontrol, rol menü varsayılanları, kişi/birim bazlı görünürlük, güvenlik ve denetim ekranlarının rol bazlı görünürlüğünü yönetin. Ayarlar ve teknik kontrol alanları admin yetkisinde kalmalıdır.",
        "menu_groups": ["Kullanıcı"],
        "extra_keys": [],
        "badges": [
            ("fa-solid fa-sliders", "Ayarlar: admin"),
            ("fa-solid fa-database", "DB Kontrol: admin"),
            ("fa-solid fa-file-shield", "Denetim izi: kritik işlemler"),
        ],
        "reset_text": "Ayarlar ve güvenlik rol politikasına dön",
    },
]
# BYS360_SETTINGS_MODULE_ROLE_MATRIX_V12_END


def get_assistant_role_matrix_recommended_keys(role_key):
    return set(ASSISTANT_ROLE_MATRIX_RECOMMENDED.get((role_key or "").strip(), set()))



ROLE_MATRIX_POLICY_CONFIGS = [
    {
        "key": "general",
        "section_id": "general-role-policy",
        "title": "Genel Rol Matrisi",
        "description": "Dashboard, görevler, destek talepleri, bildirimler, not karnesi, personel analizi ve genel rapor sekmelerinin hangi rollerde açık olacağını bu tablodan yönetin.",
        "menu_groups": ["Genel"],
        "extra_keys": [],
        "badges": [
            ("fa-solid fa-house", "Dashboard ve bildirimler: temel erişim"),
            ("fa-solid fa-headset", "Destek: tüm kullanıcı / yönetim ayrımı"),
            ("fa-solid fa-chart-line", "Raporlar: yönetici rolleri"),
        ],
        "reset_text": "Genel rol politikasına dön",
    },
    {
        "key": "personnel",
        "section_id": "personnel-role-policy",
        "title": "Personel Yönetimi Rol Matrisi",
        "description": "Personel listesi, birim-pozisyon yönetimi, özlük operasyonları, izin-devamsızlık ve personel raporları sekmelerinin rol bazlı görünürlüğünü yönetin. Standart personelde yönetim sekmeleri kapalı kalmalıdır.",
        "menu_groups": ["Personel Yönetimi"],
        "extra_keys": [],
        "badges": [
            ("fa-solid fa-users-gear", "Yönetim sekmeleri: yetkili roller"),
            ("fa-solid fa-user", "Personel: yönetim sekmesi kapalı"),
            ("fa-solid fa-shield-halved", "Rolsüz/özel durum: güvenli kapalı"),
        ],
        "reset_text": "Personel yönetimi rol politikasına dön",
    },
    {
        "key": "performance",
        "section_id": "performance-role-policy",
        "title": "Performans Yönetimi Rol Matrisi",
        "description": "Kriterler, dönemler, değerlendirme görevleri, görev yönetimi, hiyerarşi, ekip analizi, randevu, yayın ve geçmiş dönem aktarımı sekmelerinin rol bazlı görünürlüğünü yönetin.",
        "menu_groups": ["Performans Yönetimi"],
        "extra_keys": [],
        "badges": [
            ("fa-solid fa-list-check", "Kriter/Dönem: yetkili roller"),
            ("fa-solid fa-id-card", "Karne: yayın sonrası görünürlük"),
            ("fa-solid fa-bullhorn", "Yayın: üst yetki"),
        ],
        "reset_text": "Performans rol politikasına dön",
    },
    {
        "key": "communication",
        "section_id": "communication-role-policy",
        "title": "İletişim ve Anket Rol Matrisi",
        "description": "Mesajlar, bildirimler, anketler ve yönetim ekranlarının hangi rollerde açık olduğunu bu tablodan doğrudan yönetebilirsiniz. Mesajlar herkese açık kalacak, anket yönetimi ise yönetici rollerinde kalacak şekilde öneri matrisi hazır gelir.",
        "menu_groups": ["İletişim ve Anket Yönetimi"],
        "extra_keys": ["notifications"],
        "badges": [
            ("fa-solid fa-envelope", "Mesajlar: herkese açık"),
            ("fa-solid fa-square-poll-vertical", "Anketler: herkese açık"),
            ("fa-solid fa-lock", "Anket Yönetimi / Sonuçları: yönetici rolleri"),
        ],
        "reset_text": "İletişim ve anket rol politikasına dön",
    },
    {
        "key": "ai",
        "section_id": "ai-role-policy",
        "title": "AI Karar Destek Rol Matrisi",
        "description": "AI Karar Destek Merkezi ve ilişkili karar destek ekranlarının hangi rollerde açık olacağını yönetin. AI karar vermez; yalnızca yetkili rollere kontrollü özet ve analiz desteği sağlar.",
        "menu_groups": ["AI Karar Destek Merkezi"],
        "extra_keys": [],
        "badges": [
            ("fa-solid fa-brain", "AI: kontrollü karar destek"),
            ("fa-solid fa-user-shield", "Yetki sınırı aşılmaz"),
            ("fa-solid fa-file-shield", "Log ve redaksiyon ilkesi korunur"),
        ],
        "reset_text": "AI karar destek rol politikasına dön",
    },
    {
        "key": "settings_security",
        "section_id": "settings-security-role-policy",
        "title": "Ayarlar ve Güvenlik Rol Matrisi",
        "description": "Hesabım, Ayarlar, DB Kontrol ve Güvenli Çıkış gibi kullanıcı/ayar sekmelerinin rol bazlı görünürlüğünü yönetin. Ayarlar ve teknik kontrol alanları admin yetkisinde kalmalıdır.",
        "menu_groups": ["Kullanıcı"],
        "extra_keys": [],
        "badges": [
            ("fa-solid fa-sliders", "Ayarlar: admin"),
            ("fa-solid fa-database", "DB Kontrol: admin"),
            ("fa-solid fa-right-from-bracket", "Güvenli çıkış: tüm kullanıcılar"),
        ],
        "reset_text": "Ayarlar ve güvenlik rol politikasına dön",
    },
    {
        "key": "assistant",
        "section_id": "assistant-role-policy",
        "title": "Sanal Asistan Rol Matrisi",
        "description": "Zamanlanmış iş planlaması, hatırlatmalar, rapor oluşturma, rapor paylaşımı, AI özetleri ve asistan işlem loglarının hangi rollerde açık olacağını bu tablodan yönetin. Sanal asistan karar vermez; süreci hatırlatan, raporlayan ve kullanıcıyı yönlendiren kontrollü destek katmanı olarak çalışır.",
        "menu_groups": [],
        "extra_keys": [],
        "synthetic_items": ASSISTANT_ROLE_MATRIX_ITEMS,
        "badges": [
            ("fa-solid fa-robot", "Sanal Asistan: ayrı modül"),
            ("fa-solid fa-calendar-check", "Zamanlanmış iş ve hatırlatma"),
            ("fa-solid fa-file-export", "Rapor oluşturma ve paylaşım yetkisi"),
        ],
        "reset_text": "Sanal asistan rol politikasına dön",
    },
]


def _role_matrix_policy_config_map():
    return {config["key"]: config for config in ROLE_MATRIX_POLICY_CONFIGS}


def _find_menu_item_by_key(flat_menu_items, wanted_key):
    wanted_key = (wanted_key or "").strip()
    for item in flat_menu_items or []:
        if not isinstance(item, dict):
            continue
        if item.get("key") == wanted_key or item.get("settings_key") == wanted_key:
            return item
    return None




def _build_role_matrix_group(matrix_key, policy_items):
    config = _role_matrix_policy_config_map().get((matrix_key or "").strip())
    if not config:
        return None

    matrix = _build_communication_role_matrix(policy_items)
    matrix.update({
        "key": config["key"],
        "section_id": config["section_id"],
        "title": config["title"],
        "description": config["description"],
        "badges": config["badges"],
        "reset_text": config["reset_text"],
        "save_action": f"save_role_matrix_group__{config['key']}",
        "reset_action": f"reset_role_matrix_group__{config['key']}",
    })
    return matrix


def _build_settings_role_matrix_groups(grouped_menu_definitions, flat_menu_items):
    groups = []
    for config in ROLE_MATRIX_POLICY_CONFIGS:
        policy_items = _build_role_matrix_policy_items(grouped_menu_definitions, flat_menu_items, config["key"])
        group = _build_role_matrix_group(config["key"], policy_items)
        if group and group.get("rows"):
            groups.append(group)
    return groups


def _get_role_matrix_policy_items_or_raise(matrix_key, grouped_menu_definitions, flat_menu_items):
    config = _role_matrix_policy_config_map().get((matrix_key or "").strip())
    if not config:
        raise ValueError("Geçersiz rol matrisi grubu.")
    policy_items = _build_role_matrix_policy_items(grouped_menu_definitions, flat_menu_items, matrix_key)
    if not policy_items:
        raise ValueError(f"{config['title']} için canlı menü satırı bulunamadı.")
    return config, policy_items


def _role_matrix_form_field_name(matrix_key, role_key, menu_key):
    return f"role_matrix__{matrix_key}__{role_key}__{menu_key}"


def _collect_role_matrix_visible_keys_from_form(matrix_key, role_key, scoped_keys):
    return {
        item_key
        for item_key in scoped_keys
        if request.form.get(_role_matrix_form_field_name(matrix_key, role_key, item_key))
    }



def enforce_first_login_security_flow():
    return enforce_first_login_security_flow_redirect()




__all__ = [name for name in globals() if not name.startswith("__")]

# BYS360_ASSISTANT_ROLE_MATRIX_SETTINGS_V11_BEGIN
ASSISTANT_POLICY_ROLE_OPTIONS = [
    ("admin", "Admin"),
    ("baskan", "Başkan"),
    ("baskan_yardimcisi", "Başkan Yardımcısı"),
    ("grup_baskani", "Grup Başkanı"),
    ("mali_musavir", "Mali Müşavir"),
    ("koordinator", "Koordinatör"),
    ("birim_sorumlusu", "Birim Sorumlusu"),
    ("personel", "Personel"),
    ("kullanici", "Rolsüz/Kullanıcı"),
]

ASSISTANT_DEFAULT_VISIBLE_ROLES = {
    "admin",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "koordinator",
    "birim_sorumlusu",
}

ASSISTANT_ROLE_MATRIX_ROWS = [
    {
        "key": "assistant_module",
        "label": "Sanal Asistan Modülü",
        "icon": "fa-solid fa-sparkles",
        "description": "Ana anahtar. Kapalı rolde asistan penceresi, hızlı rehber, güvenli özet ve yönlendirme kartları görünmez.",
    },
]


def _assistant_visible_roles_from_settings():
    try:
        from app.services.assistant_settings_service import get_assistant_settings
        raw = str((get_assistant_settings() or {}).get("visible_roles") or "")
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/main_handlers/account_communication_helpers.py | line=614")
        raw = ",".join(sorted(ASSISTANT_DEFAULT_VISIBLE_ROLES))
    roles = {
        str(item or "").strip().lower().replace("ı", "i").replace("İ", "i").replace(" ", "_").replace("-", "_")
        for item in raw.replace(";", ",").replace("\n", ",").split(",")
        if str(item or "").strip()
    }
    return {role for role in roles if role and role != "__none__"}


def _build_assistant_role_matrix():
    visible_roles = _assistant_visible_roles_from_settings()
    if not visible_roles:
        visible_roles = set()
    role_rows = []
    item_rows = []
    for role_key, role_label in ASSISTANT_POLICY_ROLE_OPTIONS:
        role_rows.append({
            "role_key": role_key,
            "role_label": role_label,
            "visible_count": 1 if role_key in visible_roles else 0,
            "recommended_count": 1 if role_key in ASSISTANT_DEFAULT_VISIBLE_ROLES else 0,
        })

    for item in ASSISTANT_ROLE_MATRIX_ROWS:
        states = []
        visible_count = 0
        recommended_roles = []
        for role_key, role_label in ASSISTANT_POLICY_ROLE_OPTIONS:
            is_visible = role_key in visible_roles
            is_recommended = role_key in ASSISTANT_DEFAULT_VISIBLE_ROLES
            if is_visible:
                visible_count += 1
            if is_recommended:
                recommended_roles.append(role_label)
            states.append({
                "role_key": role_key,
                "role_label": role_label,
                "is_visible": is_visible,
                "is_recommended": is_recommended,
            })
        item_rows.append({
            "key": item["key"],
            "label": item["label"],
            "icon": item["icon"],
            "description": item["description"],
            "visible_count": visible_count,
            "states": states,
            "recommended_roles": recommended_roles,
        })

    return {
        "roles": role_rows,
        "rows": item_rows,
        "items": item_rows,
        "item_count": len(item_rows),
        "visible_roles": sorted(visible_roles),
    }


def _upsert_assistant_module_setting(setting_key, label, value_text, value_type="string", description="", updated_by_user_id=None):
    from app.models import ModuleSetting
    row = ModuleSetting.query.filter_by(module_key="assistant", setting_key=setting_key).first()
    if not row:
        row = ModuleSetting(
            module_key="assistant",
            setting_key=setting_key,
            label=label,
            value_type=value_type,
            description=description,
            is_active=True,
        )
        db.session.add(row)
    row.label = label
    row.value_text = str(value_text)
    row.value_type = value_type
    row.description = description
    row.is_active = True
    row.updated_by_user_id = updated_by_user_id
    return row


def save_assistant_role_matrix_from_form(form, *, updated_by_user_id=None):
    selected_roles = []
    for role_key, _role_label in ASSISTANT_POLICY_ROLE_OPTIONS:
        if form.get(f"assistant_role_policy__{role_key}__assistant_module"):
            selected_roles.append(role_key)

    visible_roles_value = ",".join(selected_roles) if selected_roles else "__none__"
    _upsert_assistant_module_setting(
        "enabled",
        "Sanal Asistan Aktif",
        "true",
        "bool",
        "Sanal Asistan genel aktiflik bayrağı. Rol bazlı görünürlük ayrıca visible_roles ile yönetilir.",
        updated_by_user_id=updated_by_user_id,
    )
    _upsert_assistant_module_setting(
        "visible_roles",
        "Sanal Asistan Görünür Rolleri",
        visible_roles_value,
        "string",
        "Sanal Asistan ana menüsü, penceresi ve tüm kısa yolları hangi rollerde görünecek.",
        updated_by_user_id=updated_by_user_id,
    )
    db.session.commit()
    return len(selected_roles)


def reset_assistant_role_matrix_defaults(*, updated_by_user_id=None):
    visible_roles_value = ",".join(sorted(ASSISTANT_DEFAULT_VISIBLE_ROLES))
    _upsert_assistant_module_setting(
        "enabled",
        "Sanal Asistan Aktif",
        "true",
        "bool",
        "Sanal Asistan genel aktiflik bayrağı.",
        updated_by_user_id=updated_by_user_id,
    )
    _upsert_assistant_module_setting(
        "visible_roles",
        "Sanal Asistan Görünür Rolleri",
        visible_roles_value,
        "string",
        "Önerilen rol politikası: yönetici rolleri açık, personel/kullanıcı kapalı.",
        updated_by_user_id=updated_by_user_id,
    )
    db.session.commit()
    return len(ASSISTANT_DEFAULT_VISIBLE_ROLES)
# BYS360_ASSISTANT_ROLE_MATRIX_SETTINGS_V11_END

# BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_BEGIN
# Ayarlar > Modül Bazlı Rol Matrisleri içinde Personel Yönetimi güncel canlı kapsamı.
# Canlı personel omurgası yalnızca özlük/kullanıcı kaydı, birim-pozisyon yapısı ve izin-devamsızlık/vekâlet hattıdır.
# Eski personel operasyon sekmeleri rol matrisinde gösterilmez.

PERSONNEL_ROLE_MATRIX_CURRENT_SCOPE_ITEMS = [
    {
        "key": "admin_users",
        "label": "Personel Özlük Dosyaları",
        "icon": "fa-solid fa-folder-open",
        "section": "Personel Yönetimi Rol Matrisi",
        "settings_key": "admin_users",
    },
    {
        "key": "org_units",
        "label": "Birim ve Pozisyon Yönetimi",
        "icon": "fa-solid fa-diagram-project",
        "section": "Personel Yönetimi Rol Matrisi",
        "settings_key": "org_units",
    },
    {
        "key": "hr_leave_tracking",
        "label": "İzin, Devamsızlık ve Vekâlet",
        "icon": "fa-solid fa-calendar-check",
        "section": "Personel Yönetimi Rol Matrisi",
        "settings_key": "hr_leave_tracking",
    },
]

_PERSONNEL_ROLE_MATRIX_CURRENT_SCOPE_KEYS = {item["key"] for item in PERSONNEL_ROLE_MATRIX_CURRENT_SCOPE_ITEMS}

_BYS360_PREVIOUS_EXTEND_FLAT_MENU_ITEMS_FOR_ASSISTANT = globals().get(
    "extend_flat_menu_items_with_assistant_role_matrix_items"
)


_BYS360_BASE_ROLE_MATRIX_POLICY_CONFIGS = list(globals().get("ROLE_MATRIX_POLICY_CONFIGS", []) or [])
_BYS360_PERSONNEL_POLICY_CONFIG = {
    "key": "personnel",
    "section_id": "personnel-role-policy",
    "title": "Personel Yönetimi Rol Matrisi",
    "description": "Güncel canlı kapsamda Personel Yönetimi yalnızca Personel Özlük Dosyaları, Birim ve Pozisyon Yönetimi ile İzin, Devamsızlık ve Vekâlet hattından oluşur. Kaldırılmış personel operasyon sekmeleri bu matristen temizlenmiştir.",
    "menu_groups": [],
    "extra_keys": [],
    "synthetic_items": PERSONNEL_ROLE_MATRIX_CURRENT_SCOPE_ITEMS,
    "badges": [
        ("fa-solid fa-folder-open", "Özlük ve kullanıcı kaydı: yetkili roller"),
        ("fa-solid fa-diagram-project", "Birim ve pozisyon: yönetim kapsamı"),
        ("fa-solid fa-calendar-check", "İzin, devamsızlık ve vekâlet: aktif omurga"),
    ],
    "reset_text": "Personel yönetimi güncel kapsam politikasına dön",
}

ROLE_MATRIX_POLICY_CONFIGS = [
    (_BYS360_PERSONNEL_POLICY_CONFIG if isinstance(config, dict) and config.get("key") == "personnel" else config)
    for config in _BYS360_BASE_ROLE_MATRIX_POLICY_CONFIGS
]
if not any(isinstance(config, dict) and config.get("key") == "personnel" for config in ROLE_MATRIX_POLICY_CONFIGS):
    ROLE_MATRIX_POLICY_CONFIGS.insert(0, _BYS360_PERSONNEL_POLICY_CONFIG)

_BYS360_PREVIOUS_BUILD_ROLE_MATRIX_POLICY_ITEMS = globals().get("_build_role_matrix_policy_items")

def _build_role_matrix_policy_items(grouped_menu_definitions, flat_menu_items, matrix_key):
    if (matrix_key or "").strip() == "personnel":
        return [dict(item) for item in PERSONNEL_ROLE_MATRIX_CURRENT_SCOPE_ITEMS]
    if callable(_BYS360_PREVIOUS_BUILD_ROLE_MATRIX_POLICY_ITEMS):
        return _BYS360_PREVIOUS_BUILD_ROLE_MATRIX_POLICY_ITEMS(grouped_menu_definitions, flat_menu_items, matrix_key)
    return []
# BYS360_PERSONEL_ROLE_MATRIX_CURRENT_SCOPE_V1_END

# BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1_BEGIN
# Ayarlar > Modül Bazlı Rol Matrisleri; son eklenen tüm canlı sekmeleri de kaydeder.
_BYS360_ALL_MENU_ROLE_MATRIX_ITEMS = [
    {'key': 'support_index', 'label': 'Yardım Merkezi', 'icon': 'fa-solid fa-circle-question', 'settings_key': 'support_index', 'section': 'Yardım Merkezi ve Destek', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'support_new', 'label': 'Yeni Talep Aç', 'icon': 'fa-solid fa-plus', 'settings_key': 'support_new', 'section': 'Yardım Merkezi ve Destek', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'support_my_tickets', 'label': 'Taleplerim', 'icon': 'fa-solid fa-folder-open', 'settings_key': 'support_my_tickets', 'section': 'Yardım Merkezi ve Destek', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'support_assigned', 'label': 'Bana Atananlar', 'icon': 'fa-solid fa-user-check', 'settings_key': 'support_assigned', 'section': 'Yardım Merkezi ve Destek', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'support_all', 'label': 'Tüm Talepler', 'icon': 'fa-solid fa-table-list', 'settings_key': 'support_all', 'section': 'Yardım Merkezi ve Destek', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'admin_users', 'label': 'Personel Listesi', 'icon': 'fa-solid fa-users', 'settings_key': 'admin_users', 'section': 'Personel Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'org_units', 'label': 'Birim ve Pozisyon Yönetimi', 'icon': 'fa-solid fa-sitemap', 'settings_key': 'org_units', 'section': 'Personel Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'hr_leave_tracking', 'label': 'İzin ve Devamsızlık Takibi', 'icon': 'fa-solid fa-calendar-check', 'settings_key': 'hr_leave_tracking', 'section': 'Personel Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_scorecard', 'label': 'Not Karnesi', 'icon': 'fa-solid fa-id-card', 'settings_key': 'performance_scorecard', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'my_performance_comparison', 'label': 'Kişisel / Grup Ortalaması', 'icon': 'fa-solid fa-chart-line', 'settings_key': 'my_performance_comparison', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'performance_reports', 'label': 'Performans Raporları', 'icon': 'fa-solid fa-chart-pie', 'settings_key': 'performance_reports', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_tasks', 'label': 'Görevlerim', 'icon': 'fa-solid fa-list-check', 'settings_key': 'performance_tasks', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_criteria', 'label': 'Değerlendirme Kriterleri', 'icon': 'fa-solid fa-list-ul', 'settings_key': 'performance_criteria', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi']},
    {'key': 'performance_periods', 'label': 'Dönemler ve Kapsamlar', 'icon': 'fa-solid fa-calendar-days', 'settings_key': 'performance_periods', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi']},
    {'key': 'performance_evaluation_tasks', 'label': 'Değerlendirme Görevleri', 'icon': 'fa-solid fa-clipboard-check', 'settings_key': 'performance_evaluation_tasks', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_task_management', 'label': 'Görev Yönetimi', 'icon': 'fa-solid fa-screwdriver-wrench', 'settings_key': 'performance_task_management', 'section': 'Performans Yönetimi', 'required_roles': ['admin']},
    {'key': 'performance_hierarchy_tree', 'label': 'Hiyerarşi Ağacı', 'icon': 'fa-solid fa-sitemap', 'settings_key': 'performance_hierarchy_tree', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_hierarchy_assignments', 'label': 'Hiyerarşi Atamaları', 'icon': 'fa-solid fa-code-branch', 'settings_key': 'performance_hierarchy_assignments', 'section': 'Performans Yönetimi', 'required_roles': ['admin']},
    {'key': 'performance_team_compare', 'label': 'Ekip / Personel Analizi', 'icon': 'fa-solid fa-people-arrows', 'settings_key': 'performance_team_compare', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'team_performance_comparison_history', 'label': 'Personel Dönem Analizi', 'icon': 'fa-solid fa-code-compare', 'settings_key': 'team_performance_comparison_history', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_feedback_meetings', 'label': 'Geri Bildirim Talepleri ve Randevu', 'icon': 'fa-solid fa-comments', 'settings_key': 'performance_feedback_meetings', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_publish', 'label': 'Yayın Yönetimi', 'icon': 'fa-solid fa-bullhorn', 'settings_key': 'performance_publish', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan']},
    {'key': 'performance_president_approvals', 'label': 'Başkan Onayları', 'icon': 'fa-solid fa-stamp', 'settings_key': 'performance_president_approvals', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan']},
    {'key': 'performance_personnel_support_publish_approval', 'label': 'Yayın Ön Onayı', 'icon': 'fa-solid fa-user-check', 'settings_key': 'performance_personnel_support_publish_approval', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'grup_baskani', 'personel_ve_destek_hizmetleri_grup_baskani', 'personel_destek_hizmetleri_grup_baskani', 'personel_ve_idari_isler_grup_baskani', 'personel_idari_isler_grup_baskani']},
    {'key': 'performance_process_tracking', 'label': 'Süreç Takibi', 'icon': 'fa-solid fa-route', 'settings_key': 'performance_process_tracking', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_process_reports', 'label': 'Süreç Raporları', 'icon': 'fa-solid fa-chart-line', 'settings_key': 'performance_process_reports', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_interim_notes', 'label': 'Dönem İçi Notlar', 'icon': 'fa-regular fa-note-sticky', 'settings_key': 'performance_interim_notes', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_development_guidance', 'label': 'Gelişim Rehberi', 'icon': 'fa-solid fa-seedling', 'settings_key': 'performance_development_guidance', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_meeting_p3_reminders', 'label': 'Hatırlatma ve Aksatan Amirler', 'icon': 'fa-solid fa-bell', 'settings_key': 'performance_meeting_p3_reminders', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_archive', 'label': 'Geçmiş Karne Arşivi', 'icon': 'fa-solid fa-box-archive', 'settings_key': 'performance_archive', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'performance_history_import', 'label': 'Geçmiş Puan Aktarımı', 'icon': 'fa-solid fa-file-import', 'settings_key': 'performance_history_import', 'section': 'Performans Yönetimi', 'required_roles': ['admin']},
    {'key': 'performance_mail_settings', 'label': 'Performans Mail Ayarları', 'icon': 'fa-solid fa-envelope-open-text', 'settings_key': 'performance_mail_settings', 'section': 'Performans Yönetimi', 'required_roles': ['admin']},
    {'key': 'performance_kpi_dashboard', 'label': 'KPI Dashboardu', 'icon': 'fa-solid fa-gauge-high', 'settings_key': 'performance_kpi_dashboard', 'section': 'KPI ve Hedef Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_kpi_management', 'label': 'KPI ve Hedef Yönetimi', 'icon': 'fa-solid fa-bullseye', 'settings_key': 'performance_kpi_management', 'section': 'KPI ve Hedef Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator']},
    {'key': 'performance_competency_library', 'label': 'Yetkinlik Kütüphanesi', 'icon': 'fa-solid fa-layer-group', 'settings_key': 'performance_competency_library', 'section': 'KPI ve Hedef Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'performance_self_assessment', 'label': 'Öz Değerlendirme', 'icon': 'fa-solid fa-user-pen', 'settings_key': 'performance_self_assessment', 'section': 'KPI ve Hedef Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'performance_kpi_analysis', 'label': 'KPI Analiz Merkezi', 'icon': 'fa-solid fa-chart-pie', 'settings_key': 'performance_kpi_analysis', 'section': 'KPI ve Hedef Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator']},
    {'key': 'ai_agent_panel', 'label': 'BYS360 Asistanı Modülü', 'icon': 'fa-solid fa-robot', 'settings_key': 'ai_agent_panel', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'ai_teaching_center', 'label': 'Asistan Öğretim Merkezi', 'icon': 'fa-solid fa-graduation-cap', 'settings_key': 'ai_teaching_center', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan']},
    {'key': 'assistant_center', 'label': 'Sanal Asistan Merkezi', 'icon': 'fa-solid fa-robot', 'settings_key': 'assistant_center', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'assistant_quick_help', 'label': 'Hızlı Rehber Cevapları', 'icon': 'fa-solid fa-circle-question', 'settings_key': 'assistant_quick_help', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'assistant_my_summary', 'label': 'Benim Özetim Kartları', 'icon': 'fa-solid fa-gauge-high', 'settings_key': 'assistant_my_summary', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'assistant_support_routing', 'label': 'Yardım Merkezi Yönlendirmesi', 'icon': 'fa-solid fa-headset', 'settings_key': 'assistant_support_routing', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'assistant_performance_guidance', 'label': 'Performans Süreç Rehberi', 'icon': 'fa-solid fa-chart-line', 'settings_key': 'assistant_performance_guidance', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'assistant_president_approval_guidance', 'label': 'Başkan Onayı Rehberi', 'icon': 'fa-solid fa-stamp', 'settings_key': 'assistant_president_approval_guidance', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan']},
    {'key': 'assistant_publish_preapproval_guidance', 'label': 'Yayın Ön Onayı Rehberi', 'icon': 'fa-solid fa-user-check', 'settings_key': 'assistant_publish_preapproval_guidance', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'grup_baskani', 'personel_ve_destek_hizmetleri_grup_baskani', 'personel_destek_hizmetleri_grup_baskani', 'personel_ve_idari_isler_grup_baskani', 'personel_idari_isler_grup_baskani']},
    {'key': 'assistant_interim_notes_guidance', 'label': 'Dönem İçi Not Rehberi', 'icon': 'fa-regular fa-note-sticky', 'settings_key': 'assistant_interim_notes_guidance', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'assistant_development_guidance', 'label': 'Gelişim Rehberi', 'icon': 'fa-solid fa-seedling', 'settings_key': 'assistant_development_guidance', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'assistant_archive_guidance', 'label': 'Geçmiş Karne Arşivi Rehberi', 'icon': 'fa-solid fa-box-archive', 'settings_key': 'assistant_archive_guidance', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'assistant_process_alerts', 'label': 'Süreç Hatırlatma ve Uyarılar', 'icon': 'fa-solid fa-triangle-exclamation', 'settings_key': 'assistant_process_alerts', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'assistant_my_reminders', 'label': 'Hatırlatmalarım', 'icon': 'fa-solid fa-bell', 'settings_key': 'assistant_my_reminders', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'assistant_scheduled_tasks', 'label': 'Zamanlanmış İşler', 'icon': 'fa-solid fa-calendar-check', 'settings_key': 'assistant_scheduled_tasks', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'assistant_report_generate', 'label': 'Rapor Oluşturma', 'icon': 'fa-solid fa-file-lines', 'settings_key': 'assistant_report_generate', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'assistant_report_share', 'label': 'Rapor Paylaşma', 'icon': 'fa-solid fa-share-nodes', 'settings_key': 'assistant_report_share', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu']},
    {'key': 'assistant_ai_summary', 'label': 'AI Özet ve Karar Notu', 'icon': 'fa-solid fa-brain', 'settings_key': 'assistant_ai_summary', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator']},
    {'key': 'assistant_logs', 'label': 'Asistan İşlem Logları', 'icon': 'fa-solid fa-clipboard-list', 'settings_key': 'assistant_logs', 'section': 'Sanal Asistan', 'required_roles': ['admin', 'baskan']},
    {'key': 'assistant_settings', 'label': 'Asistan Ayarları', 'icon': 'fa-solid fa-sliders', 'settings_key': 'assistant_settings', 'section': 'Sanal Asistan', 'required_roles': ['admin']},
    {'key': 'settings', 'label': 'Sistem Ayarları', 'icon': 'fa-solid fa-sliders', 'settings_key': 'settings', 'section': 'Ayarlar ve Güvenlik', 'required_roles': ['admin']},
    {'key': 'db_check', 'label': 'DB Kontrol', 'icon': 'fa-solid fa-database', 'settings_key': 'db_check', 'section': 'Ayarlar ve Güvenlik', 'required_roles': ['admin']},
    {'key': 'account', 'label': 'Hesabım', 'icon': 'fa-solid fa-user', 'settings_key': 'account', 'section': 'Ayarlar ve Güvenlik', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
    {'key': 'logout', 'label': 'Güvenli Çıkış', 'icon': 'fa-solid fa-right-from-bracket', 'settings_key': 'logout', 'section': 'Ayarlar ve Güvenlik', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'personel']},
]

_BYS360_ALL_MENU_ROLE_MATRIX_ITEM_BY_KEY = {item["key"]: item for item in _BYS360_ALL_MENU_ROLE_MATRIX_ITEMS}

ROLE_MATRIX_POLICY_CONFIGS = [
    {
        "key": "general",
        "section_id": "general-role-policy",
        "title": "Genel Rol Matrisi",
        "description": "Dashboard, bildirimler, destek kısayolları, görevler, not karnesi, personel analizi ve genel rapor görünürlüğünü yönetin.",
        "menu_groups": ["Genel"],
        "extra_keys": ["notifications", "support_index", "support_new", "support_my_tickets", "support_assigned", "support_all"],
        "synthetic_items": [],
        "badges": [("fa-solid fa-house", "Genel alan"), ("fa-solid fa-headset", "Destek"), ("fa-solid fa-user-shield", "Rol bazlı")],
        "reset_text": "Genel rol politikasına dön",
    },
    {
        "key": "personnel",
        "section_id": "personnel-role-policy",
        "title": "Personel Yönetimi Rol Matrisi",
        "description": "Personel listesi, birim/pozisyon ve izin-devamsızlık/vekâlet canlı sekmelerini yönetin. Kapalı sekmeler sidebar’da görünmez.",
        "menu_groups": [],
        "extra_keys": [],
        "synthetic_items": [_BYS360_ALL_MENU_ROLE_MATRIX_ITEM_BY_KEY[k] for k in ["admin_users", "org_units", "hr_leave_tracking"] if k in _BYS360_ALL_MENU_ROLE_MATRIX_ITEM_BY_KEY],
        "badges": [("fa-solid fa-users-gear", "Canlı personel omurgası"), ("fa-solid fa-user", "Personelde yönetim kapalı"), ("fa-solid fa-shield-halved", "Ayar son karar")],
        "reset_text": "Personel yönetimi rol politikasına dön",
    },
    {
        "key": "performance",
        "section_id": "performance-role-policy",
        "title": "Performans Yönetimi Rol Matrisi",
        "description": "Kriter, dönem, görev, karne, Başkan Onayları, Yayın Ön Onayı, süreç takibi, süreç raporları, dönem içi notlar, gelişim rehberi, hatırlatma, arşiv, KPI/Hedef, yetkinlik, öz değerlendirme ve KPI analiz sekmelerini yönetin.",
        "menu_groups": [],
        "extra_keys": [],
        "synthetic_items": [_BYS360_ALL_MENU_ROLE_MATRIX_ITEM_BY_KEY[k] for k in [
            "performance_scorecard", "my_performance_comparison", "performance_reports", "performance_tasks",
            "performance_criteria", "performance_periods", "performance_evaluation_tasks", "performance_task_management",
            "performance_hierarchy_tree", "performance_hierarchy_assignments", "performance_team_compare",
            "team_performance_comparison_history", "performance_feedback_meetings", "performance_publish",
            "performance_president_approvals", "performance_personnel_support_publish_approval", "performance_process_tracking",
            "performance_process_reports", "performance_interim_notes", "performance_development_guidance", "performance_meeting_p3_reminders",
            "performance_archive", "performance_history_import", "performance_mail_settings", "performance_kpi_dashboard",
            "performance_kpi_management", "performance_competency_library", "performance_self_assessment", "performance_kpi_analysis"
        ] if k in _BYS360_ALL_MENU_ROLE_MATRIX_ITEM_BY_KEY],
        "badges": [("fa-solid fa-stamp", "Başkan Onayları"), ("fa-solid fa-route", "Süreç sekmeleri"), ("fa-solid fa-bullseye", "KPI/Hedef")],
        "reset_text": "Performans rol politikasına dön",
    },
    {
        "key": "communication",
        "section_id": "communication-role-policy",
        "title": "İletişim ve Anket Rol Matrisi",
        "description": "Mesaj, duyuru, anket, geri bildirim, nabız, kampanya, sonuç ve aksiyon ekranlarının rol bazlı görünürlüğünü yönetin.",
        "menu_groups": ["İletişim ve Anket Yönetimi"],
        "extra_keys": ["notifications"],
        "synthetic_items": [],
        "badges": [("fa-solid fa-envelope", "Mesaj"), ("fa-solid fa-square-poll-vertical", "Anket"), ("fa-solid fa-chart-column", "Sonuç")],
        "reset_text": "İletişim ve anket rol politikasına dön",
    },
    {
        "key": "ai",
        "section_id": "ai-role-policy",
        "title": "AI Karar Destek Rol Matrisi",
        "description": "AI Karar Destek Merkezi ve AI öğretim/analiz görünürlüğünü yönetin. AI karar vermez; yalnızca yetkili özet sağlar.",
        "menu_groups": ["AI Karar Destek Merkezi"],
        "extra_keys": ["ai_center", "ai_teaching_center"],
        "synthetic_items": [],
        "badges": [("fa-solid fa-brain", "AI karar vermez"), ("fa-solid fa-user-shield", "Yetki sınırı"), ("fa-solid fa-file-shield", "Log")],
        "reset_text": "AI karar destek rol politikasına dön",
    },
    {
        "key": "assistant",
        "section_id": "assistant-role-policy",
        "title": "BYS360 Asistanı Rol Matrisi",
        "description": "BYS360 Asistanı Modülü, öğretim merkezi, rehber cevap, güvenli özet, performans rehberi, Başkan Onayı, yayın ön onayı, dönem içi not, gelişim ve rapor yetkilerini yönetin.",
        "menu_groups": [],
        "extra_keys": [],
        "synthetic_items": [_BYS360_ALL_MENU_ROLE_MATRIX_ITEM_BY_KEY[k] for k in [
            "ai_agent_panel", "ai_teaching_center", "assistant_center", "assistant_quick_help", "assistant_my_summary",
            "assistant_support_routing", "assistant_performance_guidance", "assistant_president_approval_guidance",
            "assistant_publish_preapproval_guidance", "assistant_interim_notes_guidance", "assistant_development_guidance",
            "assistant_archive_guidance", "assistant_process_alerts", "assistant_my_reminders", "assistant_scheduled_tasks",
            "assistant_report_generate", "assistant_report_share", "assistant_ai_summary", "assistant_logs", "assistant_settings"
        ] if k in _BYS360_ALL_MENU_ROLE_MATRIX_ITEM_BY_KEY],
        "badges": [("fa-solid fa-robot", "Asistan"), ("fa-solid fa-gauge-high", "Güvenli özet"), ("fa-solid fa-route", "Yönlendirme")],
        "reset_text": "BYS360 Asistanı rol politikasına dön",
    },
    {
        "key": "settings_security",
        "section_id": "settings-security-role-policy",
        "title": "Ayarlar ve Güvenlik Rol Matrisi",
        "description": "Hesabım, Ayarlar, DB Kontrol ve Güvenli Çıkış görünürlüğünü yönetin. Ayarlar ve teknik kontrol admin yetkisinde kalmalıdır.",
        "menu_groups": ["Kullanıcı"],
        "extra_keys": ["account", "settings", "db_check", "logout"],
        "synthetic_items": [],
        "badges": [("fa-solid fa-sliders", "Ayarlar"), ("fa-solid fa-database", "DB"), ("fa-solid fa-right-from-bracket", "Çıkış")],
        "reset_text": "Ayarlar ve güvenlik rol politikasına dön",
    },
]

# BYS360_SETTINGS_MENU_ROLE_MATRIX_ALL_TABS_V1_END

# BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_BEGIN
# BYS360 Asistanı'nın gerçek sol menü sekmeleri Ayarlar > Sanal Asistan Rol Matrisi kapsamına alındı.
_BYS360_ASSISTANT_TAB_ROLE_MATRIX_ITEMS = [
    {"key": "assistant_module", "label": "BYS360 Asistanı Modülü Ana Anahtarı", "icon": "fa-solid fa-toggle-on", "section": "BYS360 Asistanı"},
    {"key": "ai_agent_panel", "label": "Asistan Paneli", "icon": "fa-solid fa-robot", "section": "BYS360 Asistanı"},
    {"key": "ai_agent_knowledge", "label": "Asistan Bilgi Bankası", "icon": "fa-solid fa-book-open-reader", "section": "BYS360 Asistanı"},
    {"key": "ai_agent_teaching_center", "label": "Asistan Öğretim Merkezi", "icon": "fa-solid fa-chalkboard-user", "section": "BYS360 Asistanı"},
]
try:
    _existing = {_item.get("key") for _item in ASSISTANT_ROLE_MATRIX_ITEMS if isinstance(_item, dict)}
    _new_items = []
    for _item in _BYS360_ASSISTANT_TAB_ROLE_MATRIX_ITEMS:
        if _item["key"] not in _existing:
            _new_items.append(dict(_item))
            _existing.add(_item["key"])
    ASSISTANT_ROLE_MATRIX_ITEMS = _new_items + list(ASSISTANT_ROLE_MATRIX_ITEMS)
    ASSISTANT_ROLE_MATRIX_KEYS = {_item["key"] for _item in ASSISTANT_ROLE_MATRIX_ITEMS if isinstance(_item, dict) and _item.get("key")}
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_communication_helpers.py)")

_BYS360_ASSISTANT_TAB_RECOMMENDED = {
    "admin": {'assistant_module', 'ai_agent_panel', 'ai_agent_knowledge', 'ai_agent_teaching_center', 'ai_teaching_center', 'assistant_center', 'assistant_quick_help', 'assistant_my_summary', 'assistant_support_routing', 'assistant_performance_guidance', 'assistant_president_approval_guidance', 'assistant_publish_preapproval_guidance', 'assistant_interim_notes_guidance', 'assistant_development_guidance', 'assistant_archive_guidance', 'assistant_process_alerts', 'assistant_my_reminders', 'assistant_scheduled_tasks', 'assistant_report_generate', 'assistant_report_share', 'assistant_ai_summary', 'assistant_logs', 'assistant_settings'},
    "baskan": {'assistant_module', 'ai_agent_panel', 'ai_agent_knowledge', 'ai_agent_teaching_center', 'ai_teaching_center', 'assistant_center', 'assistant_quick_help', 'assistant_my_summary', 'assistant_support_routing', 'assistant_performance_guidance', 'assistant_president_approval_guidance', 'assistant_publish_preapproval_guidance', 'assistant_process_alerts', 'assistant_report_generate', 'assistant_report_share', 'assistant_ai_summary', 'assistant_logs'},
    "baskan_yardimcisi": {'assistant_module', 'ai_agent_panel', 'assistant_center', 'assistant_quick_help', 'assistant_my_summary', 'assistant_support_routing', 'assistant_performance_guidance', 'assistant_publish_preapproval_guidance', 'assistant_interim_notes_guidance', 'assistant_development_guidance', 'assistant_process_alerts', 'assistant_report_generate', 'assistant_ai_summary'},
    "grup_baskani": {'assistant_module', 'ai_agent_panel', 'assistant_center', 'assistant_quick_help', 'assistant_my_summary', 'assistant_support_routing', 'assistant_performance_guidance', 'assistant_publish_preapproval_guidance', 'assistant_interim_notes_guidance', 'assistant_development_guidance', 'assistant_archive_guidance', 'assistant_process_alerts', 'assistant_my_reminders'},
    "mali_musavir": {'assistant_module', 'ai_agent_panel', 'assistant_center', 'assistant_quick_help', 'assistant_my_summary', 'assistant_support_routing', 'assistant_performance_guidance', 'assistant_process_alerts', 'assistant_report_generate', 'assistant_ai_summary'},
    "koordinator": {'assistant_module', 'ai_agent_panel', 'assistant_center', 'assistant_quick_help', 'assistant_my_summary', 'assistant_support_routing', 'assistant_performance_guidance', 'assistant_interim_notes_guidance', 'assistant_development_guidance', 'assistant_archive_guidance', 'assistant_process_alerts', 'assistant_my_reminders'},
    "birim_sorumlusu": {'assistant_module', 'ai_agent_panel', 'assistant_center', 'assistant_quick_help', 'assistant_my_summary', 'assistant_support_routing', 'assistant_performance_guidance', 'assistant_interim_notes_guidance', 'assistant_development_guidance', 'assistant_process_alerts', 'assistant_my_reminders'},
    "personel": {'assistant_module', 'ai_agent_panel', 'assistant_center', 'assistant_quick_help', 'assistant_my_summary', 'assistant_support_routing', 'assistant_archive_guidance', 'assistant_process_alerts', 'assistant_my_reminders'},
}
try:
    for _role, _keys in _BYS360_ASSISTANT_TAB_RECOMMENDED.items():
        ASSISTANT_ROLE_MATRIX_RECOMMENDED.setdefault(_role, set()).update(_keys)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_communication_helpers.py)")
try:
    for _config in ROLE_MATRIX_POLICY_CONFIGS:
        if isinstance(_config, dict) and _config.get("key") == "assistant":
            _config["title"] = "BYS360 Asistanı Rol Matrisi"
            _config["description"] = "Asistan Paneli, Asistan Bilgi Bankası, Asistan Öğretim Merkezi ve tüm rehber/özet/hatırlatma yetkilerini rol bazlı açıp kapatın. Kapalı sekmeler sol menüde görünmez."
            _config["synthetic_items"] = list(ASSISTANT_ROLE_MATRIX_ITEMS)
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_communication_helpers.py)")

# Eski tanımı geçersiz kıl: dinamik ayarlar listesi artık gerçek Asistan sekmelerini de taşır.
# BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_END

# BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3_BEGIN
# Performans Yönetimi ana anahtarı Ayarlar > Performans Rol Matrisi satırlarına eklendi.
_BYS360_PERFORMANCE_MAIN_SWITCH_ITEM = {"key": "performance_module", "label": "Performans Yönetimi Modülü Ana Anahtarı", "icon": "fa-solid fa-toggle-on"}
try:
    _existing = {_item.get("key") for _item in PERFORMANCE_ROLE_MATRIX_V12_ITEMS if isinstance(_item, dict)}
    if "performance_module" not in _existing:
        PERFORMANCE_ROLE_MATRIX_V12_ITEMS = [dict(_BYS360_PERFORMANCE_MAIN_SWITCH_ITEM)] + list(PERFORMANCE_ROLE_MATRIX_V12_ITEMS)
except Exception:
    logger.exception("BYS360 V6C guarded exception | file=app/main_handlers/account_communication_helpers.py | line=1090")
    PERFORMANCE_ROLE_MATRIX_V12_ITEMS = [dict(_BYS360_PERFORMANCE_MAIN_SWITCH_ITEM)]
try:
    for _config in ROLE_MATRIX_POLICY_CONFIGS:
        if isinstance(_config, dict) and _config.get("key") == "performance":
            _config["title"] = "Performans Yönetimi Rol Matrisi"
            _config["description"] = "Performans Yönetimi Modülü ana anahtarı ve tüm alt sekmelerin rol bazlı görünürlüğünü yönetin. Ana anahtar kapalıysa ilgili rolde performans bölümü ve performans kısayolları menüde görünmez."
            _config["menu_groups"] = []
            _config["synthetic_items"] = list(PERFORMANCE_ROLE_MATRIX_V12_ITEMS)
            _config["badges"] = [
                ("fa-solid fa-toggle-on", "Ana anahtar: tüm performans bölümü"),
                ("fa-solid fa-list-check", "Alt sekmeler: ayrı ayrı aç/kapat"),
                ("fa-solid fa-eye-slash", "Kapalı sekme menüde görünmez"),
            ]
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_communication_helpers.py)")
# BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_MATRIX_V3_END

# BYS360_GENERAL_SECTION_RESTORE_V4_BEGIN
# Rol matrisi ekranlarında Genel çekirdek satırları kaybolmasın.
try:
    _BYS360_GENERAL_CORE_ITEMS_V4 = [
        {"key": "general_section", "label": "Genel Bölümü Ana Anahtarı", "icon": "fa-solid fa-house"},
        {"key": "home", "label": "Anasayfa", "icon": "fa-solid fa-house-chimney-window"},
        {"key": "dashboard", "label": "Dashboard", "icon": "fa-solid fa-chart-line"},
    ]
    for _config in ROLE_MATRIX_POLICY_CONFIGS:
        if isinstance(_config, dict) and _config.get("key") in ["general", "genel"]:
            _existing = {_item.get("key") for _item in _config.get("synthetic_items", []) if isinstance(_item, dict)}
            _config.setdefault("synthetic_items", [])
            for _item in reversed(_BYS360_GENERAL_CORE_ITEMS_V4):
                if _item["key"] not in _existing:
                    _config["synthetic_items"].insert(0, dict(_item))
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_communication_helpers.py)")
# BYS360_GENERAL_SECTION_RESTORE_V4_END

# BYS360_GENERAL_ROLE_MATRIX_CLEAN_PERFORMANCE_V5_BEGIN
# Genel rol matrisi artık performans sekmelerini tarif etmez; performans sekmeleri Performans Yönetimi rol matrisindedir.
def _bys360_clean_general_role_matrix_performance_text_v5():
    try:
        for _config in ROLE_MATRIX_POLICY_CONFIGS:
            if not isinstance(_config, dict):
                continue
            if _config.get("key") == "general":
                _config["description"] = (
                    "Dashboard, destek talepleri ve bildirimler gibi genel/ortak ekranların rol bazlı "
                    "görünürlüğünü yönetin. Performans sekmeleri artık yalnızca Performans Yönetimi Rol Matrisi altında yönetilir."
                )
                _config["extra_keys"] = [
                    _key for _key in (_config.get("extra_keys") or [])
                    if _key not in {"performance_tasks", "performance_scorecard", "my_performance_comparison", "performance_reports"}
                ]
                _config["badges"] = [
                    ("fa-solid fa-house", "Genel alan"),
                    ("fa-solid fa-headset", "Destek talepleri"),
                    ("fa-regular fa-bell", "Bildirimler"),
                ]
            elif _config.get("key") == "performance":
                _config["description"] = (
                    "Görevlerim, Not Karnesi, Kişisel / Grup Ortalaması, Performans Raporları ve tüm "
                    "performans alt sekmelerinin rol bazlı görünürlüğünü yönetin. Kapalı sekmeler sol menüde görünmez."
                )
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_communication_helpers.py)")


_bys360_clean_general_role_matrix_performance_text_v5()
# BYS360_GENERAL_ROLE_MATRIX_CLEAN_PERFORMANCE_V5_END

# BYS360_SETTINGS_ROLE_MATRIX_ALL_FEATURES_FINAL_FIX_V1_BEGIN
# Rol matrisi kaydetme güvenliği: Ayarlar > Modül Bazlı Rol Matrisleri içinde görünen
# tüm canlı/sentetik sekmeler flat_menu_items listesine eklenir. Böylece herhangi bir
# rol matrisi grubu kaydedilirken diğer gruplara ait sonradan eklenen anahtarlar
# role_menu_defaults listesinden yanlışlıkla silinmez.
_BYS360_PREVIOUS_EXTEND_FLAT_MENU_ITEMS_ALL_FEATURES_V1 = globals().get("extend_flat_menu_items_with_assistant_role_matrix_items")


def _bys360_role_matrix_all_feature_items_v1():
    collectors = []
    try:
        collectors.extend(list(globals().get("_BYS360_ALL_MENU_ROLE_MATRIX_ITEMS", []) or []))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_communication_helpers.py)")
    try:
        for _config in globals().get("ROLE_MATRIX_POLICY_CONFIGS", []) or []:
            if isinstance(_config, dict):
                collectors.extend(list(_config.get("synthetic_items", []) or []))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_communication_helpers.py)")
    for _name in [
        "ASSISTANT_ROLE_MATRIX_ITEMS",
        "PERFORMANCE_ROLE_MATRIX_V12_ITEMS",
        "PERSONNEL_ROLE_MATRIX_CURRENT_SCOPE_ITEMS",
    ]:
        try:
            collectors.extend(list(globals().get(_name, []) or []))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_communication_helpers.py)")
    try:
        collectors.extend(list(globals().get("_BYS360_GENERAL_CORE_ITEMS_V4", []) or []))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/main_handlers/account_communication_helpers.py)")
    collectors.extend([
        {"key": "hr_management", "label": "Personel Kontrol Paneli", "icon": "fa-solid fa-users-gear", "section": "Personel Yönetimi"},
        {"key": "hr_reports", "label": "Personel Raporları", "icon": "fa-solid fa-chart-column", "section": "Personel Yönetimi"},
    ])

    result = []
    seen = set()
    for _item in collectors:
        if not isinstance(_item, dict):
            continue
        _key = (_item.get("key") or _item.get("settings_key") or "").strip()
        if not _key or _key in seen:
            continue
        _copy = dict(_item)
        _copy.setdefault("key", _key)
        _copy.setdefault("settings_key", _key)
        _copy.setdefault("section", _copy.get("group") or _copy.get("section") or "Rol Matrisi")
        result.append(_copy)
        seen.add(_key)
    return result


# BYS360_SETTINGS_ROLE_MATRIX_ALL_FEATURES_FINAL_FIX_V1_END

# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_POLICY_BEGIN
# Portal artık Ayarlar > Modül Bazlı Rol Matrisleri içinde ayrı bir grup olarak yönetilir.
PORTAL_ROLE_MATRIX_V2_12_ITEMS = [
    {"key": "portal_feed", "label": "Portal Yayın Akışı", "icon": "fa-solid fa-stream", "settings_key": "portal_feed", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]},
    {"key": "portal_people", "label": "Personel Duvarları ve Arama", "icon": "fa-solid fa-address-book", "settings_key": "portal_people", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]},
    {"key": "portal_profiles", "label": "Profilim ve Duvar Görünümü", "icon": "fa-regular fa-user", "settings_key": "portal_profiles", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]},
    {"key": "portal_post_create", "label": "Yeni Paylaşım Yayınlama", "icon": "fa-solid fa-pen-to-square", "settings_key": "portal_post_create", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]},
    {"key": "portal_wall_post", "label": "Başka Personelin Duvarına Yazma", "icon": "fa-solid fa-user-pen", "settings_key": "portal_wall_post", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]},
    {"key": "portal_post_interact", "label": "Beğeni, Yorum ve Kaydetme", "icon": "fa-regular fa-heart", "settings_key": "portal_post_interact", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]},
    {"key": "portal_post_report", "label": "Paylaşım Bildirme", "icon": "fa-regular fa-flag", "settings_key": "portal_post_report", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]},
    {"key": "portal_post_delete", "label": "Paylaşımı Yayından Kaldırma", "icon": "fa-solid fa-trash-can", "settings_key": "portal_post_delete", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]},
    {"key": "portal_groups", "label": "Portal Grupları", "icon": "fa-solid fa-user-group", "settings_key": "portal_groups", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"]},
    {"key": "portal_group_create", "label": "Grup Oluşturma", "icon": "fa-solid fa-users-gear", "settings_key": "portal_group_create", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"]},
    {"key": "portal_press_news", "label": "Basında Tarihi Alan Haber Onayı", "icon": "fa-regular fa-newspaper", "settings_key": "portal_press_news", "section": "Kurumsal Portal", "required_roles": ["admin", "super_admin", "system_admin", "sistem_yoneticisi", "administrator"]},
    {"key": "portal_moderation", "label": "Portal Yönetimi / Moderasyon", "icon": "fa-solid fa-shield-halved", "settings_key": "portal_moderation", "section": "Kurumsal Portal", "required_roles": ["admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"]},
]
_PORTAL_ROLE_MATRIX_V2_12_CONFIG = {
    "key": "portal",
    "section_id": "portal-role-policy",
    "title": "Kurumsal Portal Rol Matrisi",
    "description": "Portal yayın akışı, personel duvarları, paylaşım yapma, başkasının duvarına yazma, silme, grup oluşturma ve moderasyon yetkilerini rol bazlı yönetin.",
    "menu_groups": ["Genel"],
    "extra_keys": [],
    "synthetic_items": PORTAL_ROLE_MATRIX_V2_12_ITEMS,
    "badges": [("fa-solid fa-stream", "Yayın Akışı"), ("fa-solid fa-user-pen", "Personel Duvarları"), ("fa-solid fa-shield-halved", "Moderasyon")],
    "reset_text": "Portal rol politikasına dön",
}
try:
    ROLE_MATRIX_POLICY_CONFIGS = [
        _config for _config in ROLE_MATRIX_POLICY_CONFIGS
        if not (isinstance(_config, dict) and _config.get("key") == "portal")
    ]
    _insert_at = 1 if len(ROLE_MATRIX_POLICY_CONFIGS) > 1 else len(ROLE_MATRIX_POLICY_CONFIGS)
    ROLE_MATRIX_POLICY_CONFIGS.insert(_insert_at, _PORTAL_ROLE_MATRIX_V2_12_CONFIG)
except Exception:
    logger.exception("BYS360 V6C guarded exception | file=app/main_handlers/account_communication_helpers.py | line=1282")
    ROLE_MATRIX_POLICY_CONFIGS = [_PORTAL_ROLE_MATRIX_V2_12_CONFIG]
# BYS360_PORTAL_SETTINGS_ROLE_MATRIX_V2_12_POLICY_END

# BYS360_PERFORMANCE_V2_1_23B_SETTINGS_PERFORMANCE_POLICY_VISIBLE_BEGIN
# /settings#performance-role-policy düzeltmesi:
# Dönem Yönetim Merkezi, Canlı Değerlendirme Takibi ve Amir Hatırlatma Merkezi
# Ayarlar > Performans Yönetimi Rol Matrisi bölümünde görünür satır olarak yer alır.
_BYS360_PERFORMANCE_PERIOD_CENTER_POLICY_ITEMS_V2_1_23B = [
        {'key': 'performance_period_management_center', 'label': 'Dönem Yönetim Merkezi', 'icon': 'fa-solid fa-calendar-check', 'settings_key': 'performance_period_management_center', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir'], 'description': 'Dönem hazırlığı, kapsam kontrolü, görev üretimi, canlı takip ve hatırlatma adımlarını tek merkezden yönetir.'},
        {'key': 'performance_evaluation_live_tracking', 'label': 'Canlı Değerlendirme Takibi', 'icon': 'fa-solid fa-chart-line', 'settings_key': 'performance_evaluation_live_tracking', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'], 'description': 'Değerlendirme sürecinin ilerlemesini, bekleyen ve geciken görevleri yetki kapsamıyla izler.'},
        {'key': 'performance_evaluator_reminder_center', 'label': 'Amir Hatırlatma Merkezi', 'icon': 'fa-solid fa-bell', 'settings_key': 'performance_evaluator_reminder_center', 'section': 'Performans Yönetimi', 'required_roles': ['admin', 'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu'], 'description': 'Bekleyen veya geciken değerlendirme görevleri için hatırlatma hazırlığını ve hedef amir listesini yönetir.'}
    ]


def _bys360_merge_performance_period_center_policy_items_v2_1_23b():
    try:
        global PERFORMANCE_ROLE_MATRIX_V12_ITEMS
        try:
            _items = list(PERFORMANCE_ROLE_MATRIX_V12_ITEMS or [])
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/main_handlers/account_communication_helpers.py | line=1302")
            _items = []
        _existing = {(_item.get("key") or _item.get("settings_key")) for _item in _items if isinstance(_item, dict)}
        for _item in _BYS360_PERFORMANCE_PERIOD_CENTER_POLICY_ITEMS_V2_1_23B:
            _key = _item.get("key") or _item.get("settings_key")
            if _key and _key not in _existing:
                _items.append(dict(_item))
                _existing.add(_key)
        PERFORMANCE_ROLE_MATRIX_V12_ITEMS = _items

        for _config in globals().get("ROLE_MATRIX_POLICY_CONFIGS", []) or []:
            if not isinstance(_config, dict) or _config.get("key") != "performance":
                continue
            _config["title"] = "Performans Yönetimi Rol Matrisi"
            _config["description"] = (
                "Performans Yönetimi içindeki dönem, kapsam, görev, canlı takip, amir hatırlatma, "
                "Başkan/Üst Onay, yayın ön onayı, karne, arşiv ve rapor ekranlarının rol bazlı görünürlüğünü yönetin."
            )
            _config["menu_groups"] = []
            _synthetic = list(_config.get("synthetic_items", []) or [])
            _existing_s = {(_item.get("key") or _item.get("settings_key")) for _item in _synthetic if isinstance(_item, dict)}
            for _item in PERFORMANCE_ROLE_MATRIX_V12_ITEMS:
                if not isinstance(_item, dict):
                    continue
                _key = _item.get("key") or _item.get("settings_key")
                if _key and _key not in _existing_s:
                    _copy = dict(_item)
                    _copy.setdefault("settings_key", _key)
                    _copy.setdefault("section", "Performans Yönetimi")
                    _synthetic.append(_copy)
                    _existing_s.add(_key)
            _config["synthetic_items"] = _synthetic
            _config["badges"] = [
                ("fa-solid fa-calendar-check", "Dönem merkezi"),
                ("fa-solid fa-chart-line", "Canlı takip"),
                ("fa-solid fa-bell", "Hatırlatma yönetimi"),
            ]
    except Exception:
        __import__("logging").getLogger(__name__).exception(
            "BYS360 kalite denetimi: performans rol matrisi görünür satır senkronu başarısız"
        )


_bys360_merge_performance_period_center_policy_items_v2_1_23b()

_BYS360_PREVIOUS_EXTEND_FLAT_MENU_ITEMS_V2_1_23B = globals().get("extend_flat_menu_items_with_assistant_role_matrix_items")


def extend_flat_menu_items_with_assistant_role_matrix_items(flat_menu_items):
    """Ayarlar rol matrisi kayıt listesine yeni performans merkezi satırlarını da dahil eder."""
    if flat_menu_items is None:
        flat_menu_items = []
    elif not isinstance(flat_menu_items, list):
        flat_menu_items = list(flat_menu_items)

    _previous = _BYS360_PREVIOUS_EXTEND_FLAT_MENU_ITEMS_V2_1_23B
    if callable(_previous):
        try:
            flat_menu_items = _previous(flat_menu_items)
        except Exception:
            __import__("logging").getLogger(__name__).exception(
                "BYS360 kalite denetimi: önceki flat menü genişletme katmanı çalışmadı"
            )

    _existing = {(_item.get("key") or _item.get("settings_key")) for _item in flat_menu_items if isinstance(_item, dict)}
    for _item in _BYS360_PERFORMANCE_PERIOD_CENTER_POLICY_ITEMS_V2_1_23B:
        _key = _item.get("key") or _item.get("settings_key")
        if not _key or _key in _existing:
            continue
        _copy = dict(_item)
        _copy.setdefault("settings_key", _key)
        _copy.setdefault("section", "Performans Yönetimi")
        flat_menu_items.append(_copy)
        _existing.add(_key)
    return flat_menu_items
# BYS360_PERFORMANCE_V2_1_23B_SETTINGS_PERFORMANCE_POLICY_VISIBLE_END

