from __future__ import annotations

# --- BYS360 third-manager Excel import compatibility patch ---


THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]

"""Performans hiyerarşi ekranları için saf yardımcılar.

Neden var:
- Route içindeki filtreleme, gruplayama ve eksik zincir tespiti aynı dosyada büyümüştü.
- Aynı mantığın test edilmesini kolaylaştırmak için saf fonksiyonlara ayrıldı.

Ne zaman kaldırılabilir:
- Hiyerarşi ekranları tamamen domain seviyesinde yeni bir workspace'e taşındığında.

Bağımlı olduğu:
- app.performance.hierarchy_ui_routes
"""

from collections import OrderedDict
from typing import Iterable

SPECIAL_SINGLE_MANAGER_UNITS = {"HUKUK MÜŞAVİRLİĞİ", "DANIŞMANLIK", "İÇ DENETİM", "ÖZEL KALEM"}
SPECIAL_TOP_ROLES = {"baskan", "baskan_yardimcisi"}


def display_name(user) -> str:
    if not user:
        return "-"
    full_name = (getattr(user, "full_name", None) or "").strip()
    if full_name:
        return full_name
    return f"{(getattr(user, 'ad', '') or '').strip()} {(getattr(user, 'soyad', '') or '').strip()}".strip() or (getattr(user, "email", None) or "-")


def manager_map(users: Iterable[object]) -> dict[str, object]:
    mapping: dict[str, object] = {}
    for user in users:
        sicil = (getattr(user, "sicil_no", None) or "").strip()
        if sicil:
            mapping[sicil] = user
    return mapping


def row_for_user(
    user,
    by_sicil: dict[str, object],
    *,
    special_single_manager_units: set[str] | None = None,
    special_top_roles: set[str] | None = None,
) -> dict[str, object]:
    special_single_manager_units = special_single_manager_units or SPECIAL_SINGLE_MANAGER_UNITS
    special_top_roles = special_top_roles or SPECIAL_TOP_ROLES

    m1_sicil = (getattr(user, "yonetici_sicil", None) or "").strip()
    m2_sicil = (getattr(user, "ikinci_yonetici_sicil", None) or "").strip()
    m3_sicil = (getattr(user, "ucuncu_yonetici_sicil", None) or "").strip()
    m1 = by_sicil.get(m1_sicil)
    m2 = by_sicil.get(m2_sicil)
    m3 = by_sicil.get(m3_sicil)

    birim = (getattr(user, "birim", None) or "").strip()
    role = (getattr(user, "role", None) or "personel").strip().lower()

    is_single_manager_case = birim in special_single_manager_units or role in special_top_roles
    issues: list[str] = []
    if role == "baskan":
        pass
    elif is_single_manager_case:
        if not m1:
            issues.append("1. amir yok")
    else:
        if not m1:
            issues.append("1. amir yok")
        if not m2:
            issues.append("2. amir yok")

    return {
        "user": user,
        "manager_1": m1,
        "manager_2": m2,
        "manager_3": m3,
        "issues": issues,
        "is_single_manager_case": is_single_manager_case,
    }


def filter_users(users: Iterable[object], *, q: str = "", birim: str = "") -> list[object]:
    q = (q or "").strip().lower()
    birim = (birim or "").strip()

    filtered: list[object] = []
    for user in users:
        if q:
            text = " ".join([
                display_name(user),
                (getattr(user, "sicil_no", None) or ""),
                (getattr(user, "birim", None) or ""),
                (getattr(user, "ust_birim", None) or ""),
                (getattr(user, "unvan", None) or ""),
                (getattr(user, "email", None) or ""),
            ]).lower()
            if q not in text:
                continue
        if birim and (getattr(user, "birim", None) or "").strip() != birim:
            continue
        filtered.append(user)
    return filtered


def build_grouped_tree(users: Iterable[object]) -> dict[str, object]:
    grouped_tree: OrderedDict[str, OrderedDict[str, list[object]]] = OrderedDict()
    active_count = 0
    passive_count = 0

    for user in users:
        parent_name = (getattr(user, "ust_birim", None) or "Üst Birim Tanımsız").strip() or "Üst Birim Tanımsız"
        child_name = (getattr(user, "birim", None) or "Birim Tanımsız").strip() or "Birim Tanımsız"
        grouped_tree.setdefault(parent_name, OrderedDict())
        grouped_tree[parent_name].setdefault(child_name, [])
        grouped_tree[parent_name][child_name].append(user)
        if bool(getattr(user, "is_active", True)):
            active_count += 1
        else:
            passive_count += 1

    birimler = sorted({(getattr(user, 'birim', None) or '').strip() for user in users if (getattr(user, 'birim', None) or '').strip()})
    return {
        "grouped_tree": grouped_tree,
        "birimler": birimler,
        "parent_count": len(grouped_tree),
        "active_count": active_count,
        "passive_count": passive_count,
        "total_user_count": len(list(users)) if not isinstance(users, list) else len(users),
    }


def build_assignment_rows(users: Iterable[object], *, q: str = "", birim: str = "") -> dict[str, object]:
    all_users = list(users)
    by_sicil = manager_map(all_users)
    filtered = filter_users(all_users, q=q, birim=birim)
    rows = [row_for_user(user, by_sicil) for user in filtered]
    incomplete_users = [row for row in rows if row["issues"]]
    birimler = sorted({(getattr(user, 'birim', None) or '').strip() for user in all_users if (getattr(user, 'birim', None) or '').strip()})
    stats = {
        "total_count": len(all_users),
        "filtered_count": len(filtered),
        "complete_count": len(filtered) - len(incomplete_users),
        "incomplete_count": len(incomplete_users),
    }
    return {
        "all_users": all_users,
        "filtered_users": filtered,
        "rows": rows,
        "incomplete_users": incomplete_users,
        "birimler": birimler,
        "stats": stats,
        "by_sicil": by_sicil,
    }