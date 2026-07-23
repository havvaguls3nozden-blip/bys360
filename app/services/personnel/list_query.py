
"""Personel listeleme, arama ve filtreleme servis köprüsü.

Faz 2 kapsamı:
- /personnel listeleme ekranındaki q/birim/durum/rol filtrelerini servis katmanına alır.
- Template'e giden stats, user_rows, role_values ve birimler bağlamını tek yerde üretir.
- Model yazmaz, commit/rollback çalıştırmaz, kayıt/silme/fotoğraf davranışına dokunmaz.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from sqlalchemy import or_

from .categories import PERSONNEL_CATEGORY_OPTIONS, get_user_personnel_category_label


@dataclass(frozen=True, slots=True)
class PersonnelListFilters:
    q: str = ""
    birim: str = ""
    durum: str = ""
    rol: str = ""
    kategori: str = ""  # BYS360_PERSONNEL_CATEGORY_LIST_BINDING

    @property
    def has_active_filter(self) -> bool:
        return bool(self.q or self.birim or self.durum or self.rol or self.kategori)

    def to_dict(self) -> dict[str, str | bool]:
        data = asdict(self)
        data["has_active_filter"] = self.has_active_filter
        return data


@dataclass(frozen=True, slots=True)
class PersonnelListRow:
    id: int | None
    ad: str
    soyad: str
    full_name: str
    email: str
    sicil_no: str
    unvan: str
    birim: str
    ust_birim: str
    role_text: str
    personnel_category: str
    is_active: bool
    avatar_url: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PersonnelListStats:
    total_count: int
    active_count: int
    passive_count: int
    unit_count: int
    filtered_count: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def _args_get(args: Mapping[str, Any], key: str, default: str = "") -> Any:
    getter = getattr(args, "get", None)
    if callable(getter):
        return getter(key, default)
    return args.get(key, default)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def read_personnel_list_filters(args: Mapping[str, Any]) -> PersonnelListFilters:
    """Read list filters from request.args-like mapping without side effects."""
    return PersonnelListFilters(
        q=_clean_text(_args_get(args, "q")),
        birim=_clean_text(_args_get(args, "birim")),
        durum=_clean_text(_args_get(args, "durum")),
        rol=_clean_text(_args_get(args, "rol")),
        kategori=_clean_text(_args_get(args, "kategori")),
    )


def apply_personnel_list_filters(query: Any, user_model: Any, filters: PersonnelListFilters) -> Any:
    """Apply the same filters used by the legacy route, without executing the query."""
    if filters.q:
        like = f"%{filters.q}%"
        query = query.filter(
            or_(
                user_model.ad.ilike(like),
                user_model.soyad.ilike(like),
                user_model.email.ilike(like),
                user_model.sicil_no.ilike(like),
                user_model.unvan.ilike(like),
                user_model.birim.ilike(like),
                user_model.ust_birim.ilike(like),
            )
        )

    if filters.birim:
        query = query.filter(user_model.birim == filters.birim)
    if filters.durum == "aktif":
        query = query.filter(user_model.is_active.is_(True))
    elif filters.durum == "pasif":
        query = query.filter(user_model.is_active.is_(False))
    if filters.rol:
        query = query.filter(user_model.role == filters.rol)
    if filters.kategori and hasattr(user_model, "personnel_category"):
        query = query.filter(user_model.personnel_category == filters.kategori)

    return query


def build_personnel_list_base_query(user_model: Any) -> Any:
    """Return the non-admin personnel base query used by the live list screen."""
    return user_model.query.filter(user_model.role != "admin")


def _full_name_for(user: Any) -> str:
    full_name = _clean_text(getattr(user, "full_name", ""))
    if full_name:
        return full_name
    return f"{getattr(user, 'ad', '') or ''} {getattr(user, 'soyad', '') or ''}".strip()


def build_personnel_list_row(user: Any) -> dict[str, Any]:
    """Convert a User model instance to the template row contract."""
    row = PersonnelListRow(
        id=getattr(user, "id", None),
        ad=getattr(user, "ad", "") or "",
        soyad=getattr(user, "soyad", "") or "",
        full_name=_full_name_for(user),
        email=getattr(user, "email", None) or "-",
        sicil_no=getattr(user, "sicil_no", None) or "-",
        unvan=getattr(user, "unvan", None) or "-",
        birim=getattr(user, "birim", None) or "-",
        ust_birim=getattr(user, "ust_birim", None) or "-",
        role_text=getattr(user, "role_label", None) or getattr(user, "role", None) or "-",
        personnel_category=get_user_personnel_category_label(user),
        is_active=bool(getattr(user, "is_active", False)),
        avatar_url=getattr(user, "profile_photo_url", None),
    )
    return row.to_dict()


def build_personnel_list_rows(users: list[Any]) -> list[dict[str, Any]]:
    return [build_personnel_list_row(user) for user in users]


def build_personnel_list_stats(*, all_users: list[Any], filtered_users: list[Any]) -> dict[str, int]:
    stats = PersonnelListStats(
        total_count=len(all_users),
        active_count=sum(1 for user in all_users if bool(getattr(user, "is_active", False))),
        passive_count=sum(1 for user in all_users if not bool(getattr(user, "is_active", False))),
        unit_count=len({(getattr(user, "birim", "") or "").strip() for user in all_users if (getattr(user, "birim", "") or "").strip()}),
        filtered_count=len(filtered_users),
    )
    return stats.to_dict()


def build_personnel_unit_options(all_users: list[Any]) -> list[str]:
    return sorted({
        (getattr(user, "birim", "") or "").strip()
        for user in all_users
        if (getattr(user, "birim", "") or "").strip()
    })


def build_personnel_role_values(*, db_session: Any, user_model: Any) -> list[str]:
    rows = (
        db_session.query(user_model.role)
        .filter(user_model.role.isnot(None), user_model.role != "", user_model.role != "admin")
        .distinct()
        .order_by(user_model.role.asc())
        .all()
    )
    return [row[0] for row in rows if row and row[0]]


def build_personnel_list_context(*, request_args: Mapping[str, Any], user_model: Any, db_session: Any) -> dict[str, Any]:
    """Build the complete personnel list context used by app.admin.routes.personnel_list."""
    filters = read_personnel_list_filters(request_args)
    query = apply_personnel_list_filters(build_personnel_list_base_query(user_model), user_model, filters)
    users = query.order_by(user_model.ad.asc(), user_model.soyad.asc()).all()
    all_users = build_personnel_list_base_query(user_model).all()
    role_values = build_personnel_role_values(db_session=db_session, user_model=user_model)
    birimler = build_personnel_unit_options(all_users)
    stats = build_personnel_list_stats(all_users=all_users, filtered_users=users)
    user_rows = build_personnel_list_rows(users)

    return {
        "stats": stats,
        "user_rows": user_rows,
        "q": filters.q,
        "selected_birim": filters.birim,
        "selected_durum": filters.durum,
        "selected_rol": filters.rol,
        "selected_kategori": filters.kategori,
        "category_choices": [(item, item) for item in PERSONNEL_CATEGORY_OPTIONS],
        "birimler": birimler,
        "role_values": role_values,
        "role_choices": [(value, value) for value in role_values],
        "personnel_list_filters": filters.to_dict(),
        "personnel_list_phase2_summary": build_personnel_list_phase2_summary(),
    }


def build_personnel_list_phase2_summary() -> dict[str, Any]:
    return {
        "phase": "personnel_service_faz2",
        "purpose": "list_filter_context_bridge",
        "runtime_mutation": False,
        "db_commit": False,
        "db_rollback": False,
        "route_contract": "preserved",
        "template_contract": "preserved",
        "filters": ("q", "birim", "durum", "rol", "kategori"),
    }
