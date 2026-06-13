from __future__ import annotations



from typing import Any

from app.services.hierarchy_admin_service import get_manager_scope_users

ADMIN_ROLES = {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"}
MANAGER_ROLES = ADMIN_ROLES | {"koordinator", "birim_sorumlusu"}


def _full_name(user: Any) -> str:
    if not user:
        return "-"
    full_name = (getattr(user, "full_name", None) or "").strip()
    if full_name:
        return full_name
    ad = (getattr(user, "ad", None) or "").strip()
    soyad = (getattr(user, "soyad", None) or "").strip()
    return f"{ad} {soyad}".strip() or f"Personel #{getattr(user, 'id', '-') }"


def _unit_label(user: Any) -> str:
    birim = (getattr(user, "birim", None) or "").strip()
    ust = (getattr(user, "ust_birim", None) or "").strip()
    return birim or ust or "Tanımsız Birim"


def _dedupe_users(users: list[Any]) -> list[Any]:
    rows = []
    seen = set()
    for user in users:
        user_id = getattr(user, "id", None)
        if not user_id or user_id in seen:
            continue
        seen.add(user_id)
        rows.append(user)
    rows.sort(key=lambda row: (_full_name(row).lower(), getattr(row, "id", 0)))
    return rows


def _scope_options(user: Any, has_team: bool) -> list[dict[str, str]]:
    role = (getattr(user, "role", "") or "").strip().lower()
    if role in MANAGER_ROLES:
        options = [
            {"value": "mine", "label": "Sadece Kendi Alanım", "description": "Yalnızca kendi değerlendirme kayıtlarınız gösterilir."},
            {"value": "team", "label": "Doğrudan Sorumlu Olduğum Ekip", "description": "Doğrudan yönetim kapsamınızdaki personel kayıtları gösterilir."},
            {"value": "all", "label": "Yetkili Olduğum Tüm Birimler", "description": "Yetkiniz dahilindeki tüm personel ve birimler birlikte gösterilir."},
        ]
        return options if has_team else options[:1]
    return [{"value": "mine", "label": "Sadece Kendi Alanım", "description": "Yalnızca kendi değerlendirme kayıtlarınız gösterilir."}]


def build_user_scope_context(user: Any, raw_scope_mode: str | None = None) -> dict[str, Any]:
    if not user:
        return {
            "scope_mode": "mine",
            "scope_label": "Kullanıcı yok",
            "scope_heading": "Kapsam",
            "scope_description": "Oturum bulunamadı.",
            "scope_users": [],
            "scope_user_ids": [],
            "scope_options": [],
            "scope_user_count": 0,
            "scope_unit_count": 0,
            "role_title": "Kapsam",
        }

    role = (getattr(user, "role", "") or "").strip().lower()
    role_title = {
        "admin": "Admin görünümü",
        "baskan": "Başkan görünümü",
        "baskan_yardimcisi": "Başkan Yardımcısı görünümü",
        "grup_baskani": "Grup Başkanlığı görünümü",
        "koordinator": "Koordinatör görünümü",
        "birim_sorumlusu": "Birim görünümü",
    }.get(role, "Kişisel görünüm")

    scoped_rows = _dedupe_users(list(get_manager_scope_users(user) or []))
    if getattr(user, "id", None) and not any(getattr(row, "id", None) == user.id for row in scoped_rows):
        scoped_rows = _dedupe_users([user, *scoped_rows])

    team_rows = [row for row in scoped_rows if getattr(row, "id", None) != getattr(user, "id", None)]
    options = _scope_options(user, has_team=bool(team_rows))
    allowed_modes = {item["value"] for item in options}
    scope_mode = (raw_scope_mode or "").strip().lower() or ("all" if "all" in allowed_modes else "mine")
    if scope_mode not in allowed_modes:
        scope_mode = "all" if "all" in allowed_modes else "mine"

    if scope_mode == "mine":
        scope_users = [user]
        scope_label = _full_name(user)
        scope_heading = "Kişisel görünüm"
        scope_description = "Bu seçimde yalnızca kendi değerlendirme kayıtlarınız gösterilir ve yayın işlemi bu alanla sınırlı kalır."
    elif scope_mode == "team":
        scope_users = team_rows or [user]
        scope_label = "Doğrudan ekip"
        scope_heading = "Ekip görünümü"
        scope_description = "Bu seçimde yalnızca doğrudan sorumlu olduğunuz ekip listelenir ve yayın işlemleri bu ekiple sınırlı uygulanır."
    else:
        scope_users = scoped_rows or [user]
        scope_label = "Yetkili tüm kapsam"
        scope_heading = "Kurumsal görünüm" if role in ADMIN_ROLES else "Kapsam görünümü"
        scope_description = "Bu seçimde yetkiniz dahilindeki tüm personel ve birimler birlikte gösterilir; yayın işlemleri en geniş yetki alanınız için uygulanır."

    scope_users = _dedupe_users(scope_users)
    unit_names = {
        _unit_label(row)
        for row in scope_users
        if _unit_label(row)
    }

    return {
        "scope_mode": scope_mode,
        "scope_label": scope_label,
        "scope_heading": scope_heading,
        "scope_description": scope_description,
        "scope_users": scope_users,
        "scope_user_ids": [row.id for row in scope_users if getattr(row, "id", None)],
        "scope_options": options,
        "scope_user_count": len(scope_users),
        "scope_unit_count": len(unit_names),
        "role_title": role_title,
    }