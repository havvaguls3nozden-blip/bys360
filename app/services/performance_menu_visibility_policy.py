# -*- coding: utf-8 -*-
from __future__ import annotations


from dataclasses import dataclass
from typing import Iterable, Set

@dataclass(frozen=True)
class PerformanceMenuItem:
    key: str
    label: str
    default_for_personnel: bool
    admin_only: bool = False
    description: str = ""
    parent: str = "performance"

# BYS360 Performans Yönetimi menü görünürlüğü merkezi kayıt listesi.
# Bu dosya hem klasik performans sekmelerini hem de SP-1 KPI/Hedef Yönetimi ile gelen yeni sekmeleri kapsar.
PERFORMANCE_MENU_REGISTRY = [
    PerformanceMenuItem("performance.my_scorecard", "Kendi Karnem", True, False, "Personelin yayınlanmış kendi karnesi"),
    PerformanceMenuItem("performance.my_archive", "Geçmiş Karnelerim", True, False, "Personelin kendi geçmiş performans arşivi"),
    PerformanceMenuItem("performance.self_assessment", "Öz Değerlendirme", True, False, "Personelin kendi öz değerlendirme alanı"),
    PerformanceMenuItem("performance.my_development", "Gelişim Önerilerim", True, False, "Personelin kendisine açık gelişim önerileri"),

    PerformanceMenuItem("performance.dashboard", "Performans Yönetici Dashboard", False, True, "Yönetici genel performans görünümü"),
    PerformanceMenuItem("performance.reports", "Performans Raporları", False, True, "Yönetici ve yetkili raporları"),
    PerformanceMenuItem("performance.process_tracking", "Süreç Takibi", False, True, "Canlı performans süreç takibi"),
    PerformanceMenuItem("performance.process_reports", "Süreç Raporları", False, True, "Süreç raporları ve analizleri"),
    PerformanceMenuItem("performance.president_approvals", "Başkan Onayları", False, True, "70 altı sonuç Başkan/Üst onayları"),
    PerformanceMenuItem("performance.publish_approvals", "Yayın Onayları", False, True, "Yayın ön onayı ve final yayın kontrolü"),
    PerformanceMenuItem("performance.periods", "Dönem Yönetimi", False, True, "Dönem açma/kapatma ve kapsam yönetimi"),
    PerformanceMenuItem("performance.criteria", "Değerlendirme Kriterleri", False, True, "Kriter yönetimi"),
    PerformanceMenuItem("performance.assignments", "Görev Üretimi", False, True, "Amir değerlendirme görevi üretimi"),
    PerformanceMenuItem("performance.risk_analysis", "Riskli Personel Analizi", False, True, "Düşük performans ve risk analizleri"),

    # SP-1 / KPI-Hedef Yönetimi yeni sekmeleri
    PerformanceMenuItem("performance.kpi_dashboard", "KPI Dashboardu", False, True, "KPI ve hedef özet gösterge paneli"),
    PerformanceMenuItem("performance.kpi_management", "KPI ve Hedef Yönetimi", False, True, "Hedef dönemleri, hedef kartları ve KPI yönetimi"),
    PerformanceMenuItem("performance.competency_library", "Yetkinlik Kütüphanesi", False, True, "Yetkinlik tanımları ve rol bazlı yetkinlik şablonları"),
    PerformanceMenuItem("performance.kpi_analysis", "KPI Analiz Merkezi", False, True, "KPI gerçekleşme, sapma ve risk analizleri"),

    # Geriye dönük uyumluluk anahtarları
    PerformanceMenuItem("performance.kpi_goals", "KPI / Hedef Yönetimi", False, True, "Eski KPI/Hedef yönetimi anahtarı"),
    PerformanceMenuItem("performance.ai_agent", "BYS360 Asistanı Yönetimi", False, True, "BYS360 Asistanı yönetim ve takip ekranları"),
]

KPI_MENU_KEYS: Set[str] = {
    "performance.kpi_dashboard",
    "performance.kpi_management",
    "performance.competency_library",
    "performance.self_assessment",
    "performance.kpi_analysis",
    "performance.kpi_goals",
}

DEFAULT_PERSONNEL_ALLOWED: Set[str] = {item.key for item in PERFORMANCE_MENU_REGISTRY if item.default_for_personnel}
DEFAULT_PERSONNEL_BLOCKED: Set[str] = {item.key for item in PERFORMANCE_MENU_REGISTRY if not item.default_for_personnel}
ALL_PERFORMANCE_MENU_KEYS: Set[str] = {item.key for item in PERFORMANCE_MENU_REGISTRY}

ROLE_DEFAULTS = {
    "personel": set(DEFAULT_PERSONNEL_ALLOWED),
    "employee": set(DEFAULT_PERSONNEL_ALLOWED),
    "staff": set(DEFAULT_PERSONNEL_ALLOWED),
    "koordinator": {"performance.kpi_dashboard", "performance.self_assessment", "performance.kpi_analysis"},
    "koordinatör": {"performance.kpi_dashboard", "performance.self_assessment", "performance.kpi_analysis"},
    "grup_baskani": {"performance.kpi_dashboard", "performance.kpi_management", "performance.kpi_analysis", "performance.self_assessment"},
    "grup başkanı": {"performance.kpi_dashboard", "performance.kpi_management", "performance.kpi_analysis", "performance.self_assessment"},
    "baskan": set(ALL_PERFORMANCE_MENU_KEYS),
    "başkan": set(ALL_PERFORMANCE_MENU_KEYS),
    "admin": set(ALL_PERFORMANCE_MENU_KEYS),
    "sistem_yoneticisi": set(ALL_PERFORMANCE_MENU_KEYS),
}

def normalize_keys(keys: Iterable[str] | None) -> Set[str]:
    return {str(k).strip() for k in (keys or []) if str(k).strip()}

def allowed_for_personnel(mode: str = "safe_default", custom_allowed: Iterable[str] | None = None) -> Set[str]:
    mode = (mode or "safe_default").strip()
    if mode == "full_access":
        return set(ALL_PERFORMANCE_MENU_KEYS)
    if mode == "custom":
        safe = set(DEFAULT_PERSONNEL_ALLOWED)
        safe.update(normalize_keys(custom_allowed))
        return safe
    return set(DEFAULT_PERSONNEL_ALLOWED)

def is_personnel_allowed(menu_key: str, mode: str = "safe_default", custom_allowed: Iterable[str] | None = None) -> bool:
    return menu_key in allowed_for_personnel(mode, custom_allowed)

def role_default_allowed(role_name: str) -> Set[str]:
    key = (role_name or "").strip().lower()
    return set(ROLE_DEFAULTS.get(key, set()))
