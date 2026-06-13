# -*- coding: utf-8 -*-

"""BYS360 Faz 3.1 — Performans görünürlük rol matrisi.

Bu dosya yalnızca rol matrisini ve rol profili çözümlemesini tutar.
Faz 3.2 menü görünürlüğü, Faz 3.3 backend route kontrolü ve Faz 3.4
kurumsal erişim engeli sayfası bu merkezi matrisi okuyarak ilerlemelidir.
"""
from __future__ import annotations

from typing import Any

BYS360_PHASE3_1_ROLE_MATRIX_VERSION = "2026-05-01.phase3.1.role-matrix.v1"
BYS360_PHASE3_1_ROLE_MATRIX_MARKER = "BYS360_PHASE3_1_ROLE_MATRIX"
PHASE3_ACCESS_DENIED_MESSAGE = "Bu sayfaya erişim yetkiniz bulunmamaktadır."

# Kullanıcıya gösterilecek matris.
ROLE_VISIBILITY_MATRIX: list[dict[str, str]] = [
    {
        "role_key": "personel",
        "role_label": "Personel",
        "visible_area": "Kendi karnesi + kendi grup/kategori ortalaması",
        "detail_scope": "Kişi detayı yok; yalnızca kendi kaydı ve anonim ortalama",
        "technical_management": "Hayır",
    },
    {
        "role_key": "koordinator",
        "role_label": "Koordinatör",
        "visible_area": "Kendi kapsamındaki personel ve ortalamalar",
        "detail_scope": "Kendi koordinatörlük/çalışma grubu kapsamı",
        "technical_management": "Hayır",
    },
    {
        "role_key": "grup_baskani",
        "role_label": "Grup Başkanı",
        "visible_area": "Kendi grup/üst birim kapsamı",
        "detail_scope": "Kendi grup başkanlığı ve bağlı üst birim kapsamı",
        "technical_management": "Hayır",
    },
    {
        "role_key": "baskan",
        "role_label": "Başkan",
        "visible_area": "Genel görünüm",
        "detail_scope": "Kurum geneli",
        "technical_management": "Hayır",
    },
    {
        "role_key": "admin_sistem_yoneticisi",
        "role_label": "Admin/Sistem Yöneticisi",
        "visible_area": "Genel görünüm + teknik yönetim",
        "detail_scope": "Kurum geneli ve teknik yönetim alanları",
        "technical_management": "Evet",
    },
]

# Rol adları projede farklı yazılmış olabileceği için güvenli alias yapısı.
ROLE_ALIASES: dict[str, str] = {
    "personel": "personel",
    "user": "personel",
    "standart_personel": "personel",
    "standard_user": "personel",
    "calisan": "personel",
    "çalışan": "personel",

    "koordinator": "koordinator",
    "koordinatör": "koordinator",
    "coordinator": "koordinator",
    "birim_sorumlusu": "koordinator",
    "calisma_grubu_koordinatoru": "koordinator",
    "çalışma_grubu_koordinatörü": "koordinator",

    "grup_baskani": "grup_baskani",
    "grup başkanı": "grup_baskani",
    "grup_başkanı": "grup_baskani",
    "group_head": "grup_baskani",
    "mali_musavir": "grup_baskani",
    "mali_müşavir": "grup_baskani",

    "baskan": "baskan",
    "başkan": "baskan",
    "president": "baskan",
    "baskan_yardimcisi": "baskan",
    "başkan_yardımcısı": "baskan",
    "baskan yardimcisi": "baskan",
    "başkan yardımcısı": "baskan",

    "admin": "admin_sistem_yoneticisi",
    "sistem_yoneticisi": "admin_sistem_yoneticisi",
    "sistem_yöneticisi": "admin_sistem_yoneticisi",
    "system_admin": "admin_sistem_yoneticisi",
    "super_admin": "admin_sistem_yoneticisi",
    "administrator": "admin_sistem_yoneticisi",
}

ROLE_PRIORITY: dict[str, int] = {
    "personel": 10,
    "koordinator": 20,
    "grup_baskani": 30,
    "baskan": 40,
    "admin_sistem_yoneticisi": 50,
}

GENERAL_VIEW_ROLE_KEYS = {"baskan", "admin_sistem_yoneticisi"}
TECHNICAL_MANAGEMENT_ROLE_KEYS = {"admin_sistem_yoneticisi"}
SCOPED_MANAGER_ROLE_KEYS = {"koordinator", "grup_baskani"}
PERSONNEL_ROLE_KEYS = {"personel"}


def _ascii_tr(value: str) -> str:
    return (
        value.replace("İ", "i")
        .replace("I", "i")
        .replace("ı", "i")
        .replace("Ş", "s")
        .replace("ş", "s")
        .replace("Ğ", "g")
        .replace("ğ", "g")
        .replace("Ü", "u")
        .replace("ü", "u")
        .replace("Ö", "o")
        .replace("ö", "o")
        .replace("Ç", "c")
        .replace("ç", "c")
    )


def normalize_role_value(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = " ".join(text.replace("-", "_").split())
    text = text.replace(" ", "_")
    return text


def _extract_candidate_roles(user_or_role: Any) -> list[str]:
    if user_or_role is None:
        return []
    if isinstance(user_or_role, str):
        return [user_or_role]

    candidates: list[str] = []
    for attr in ("role", "role_name", "rol", "user_role", "primary_role"):
        value = getattr(user_or_role, attr, None)
        if value:
            candidates.append(str(value))

    roles = getattr(user_or_role, "roles", None)
    if roles:
        try:
            for role in roles:
                candidates.append(str(getattr(role, "name", role)))
        except TypeError:
            candidates.append(str(roles))

    return candidates


def resolve_phase3_role_key(user_or_role: Any) -> str:
    """Kullanıcı veya rol metnini Faz 3.1 rol anahtarına çevirir.

    Tanınmayan kullanıcı güvenli tarafta kalarak personel gibi değerlendirilir.
    Birden fazla rol varsa en geniş yetki profili seçilir.
    """
    resolved = "personel"
    best_priority = ROLE_PRIORITY[resolved]

    for candidate in _extract_candidate_roles(user_or_role):
        normalized = normalize_role_value(candidate)
        ascii_normalized = _ascii_tr(normalized)
        role_key = ROLE_ALIASES.get(normalized) or ROLE_ALIASES.get(ascii_normalized)
        if not role_key:
            continue
        priority = ROLE_PRIORITY.get(role_key, 0)
        if priority > best_priority:
            resolved = role_key
            best_priority = priority

    return resolved


def get_phase3_role_matrix() -> list[dict[str, str]]:
    return [dict(row) for row in ROLE_VISIBILITY_MATRIX]


def get_phase3_visibility_profile(user_or_role: Any) -> dict[str, Any]:
    role_key = resolve_phase3_role_key(user_or_role)
    row = next((item for item in ROLE_VISIBILITY_MATRIX if item["role_key"] == role_key), ROLE_VISIBILITY_MATRIX[0])
    return {
        **row,
        "can_view_own_scorecard": True,
        "can_view_category_average_without_person_detail": True,
        "can_view_scoped_personnel_detail": role_key in SCOPED_MANAGER_ROLE_KEYS or role_key in GENERAL_VIEW_ROLE_KEYS,
        "can_view_general": role_key in GENERAL_VIEW_ROLE_KEYS,
        "can_view_technical_management": role_key in TECHNICAL_MANAGEMENT_ROLE_KEYS,
        "requires_scope_filter": role_key in SCOPED_MANAGER_ROLE_KEYS,
        "requires_own_record_only": role_key in PERSONNEL_ROLE_KEYS,
        "access_denied_message": PHASE3_ACCESS_DENIED_MESSAGE,
    }


def phase3_can_view_general(user_or_role: Any) -> bool:
    return bool(get_phase3_visibility_profile(user_or_role)["can_view_general"])


def phase3_can_view_technical_management(user_or_role: Any) -> bool:
    return bool(get_phase3_visibility_profile(user_or_role)["can_view_technical_management"])


def phase3_requires_scope_filter(user_or_role: Any) -> bool:
    return bool(get_phase3_visibility_profile(user_or_role)["requires_scope_filter"])


def phase3_requires_own_record_only(user_or_role: Any) -> bool:
    return bool(get_phase3_visibility_profile(user_or_role)["requires_own_record_only"])


def phase3_denied_message() -> str:
    return PHASE3_ACCESS_DENIED_MESSAGE


def phase3_role_matrix_summary() -> str:
    lines = ["BYS360 Faz 3.1 Rol Matrisi"]
    for row in ROLE_VISIBILITY_MATRIX:
        lines.append(f"- {row['role_label']}: {row['visible_area']}")
    return "\n".join(lines)
