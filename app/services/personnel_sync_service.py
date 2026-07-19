from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any

from app.extensions import db
from app.models import OrganizationUnit, User
from app.route_support import bool_from_form
from app.security.email_policy import corporate_email_error_message, is_allowed_corporate_email

ROLE_CHOICES: list[tuple[str, str]] = [
    ("admin", "Admin"),
    ("baskan", "Başkan"),
    ("baskan_yardimcisi", "Başkan Yardımcısı"),
    ("grup_baskani", "Grup Başkanı"),
    ("mali_musavir", "Mali Müşavir"),
    ("birim_sorumlusu", "Birim Sorumlusu"),
    ("koordinator", "Koordinatör"),
    ("personel", "Personel"),
]

ROLE_LABEL_BY_VALUE = {value: label for value, label in ROLE_CHOICES}
ROLE_VALUE_BY_NORMALIZED = {
    "admin": "admin",
    "başkan": "baskan",
    "baskan": "baskan",
    "başkan yardımcısı": "baskan_yardimcisi",
    "başkan yardimcisi": "baskan_yardimcisi",
    "baskan yardımcısı": "baskan_yardimcisi",
    "baskan yardimcisi": "baskan_yardimcisi",
    "baskan_yardimcisi": "baskan_yardimcisi",
    "grup başkanı": "grup_baskani",
    "grup baskani": "grup_baskani",
    "grup_baskani": "grup_baskani",
    "mali müşavir": "mali_musavir",
    "mali musavir": "mali_musavir",
    "mali_musavir": "mali_musavir",
    "hukuk musaviri": "mali_musavir",
    "hukuk musaviri v.": "mali_musavir",
    "sorumlu hukuk musaviri": "mali_musavir",
    "birim sorumlusu": "birim_sorumlusu",
    "birim_sorumlusu": "birim_sorumlusu",
    "koordinatör": "koordinator",
    "koordinator": "koordinator",
    "personel": "personel",
}

EXCEL_HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "sicil_no": ("sicil no", "sicil_no", "sicil", "sicilno"),
    "ad": ("ad", "adi"),
    "soyad": ("soyad", "soyadi"),
    "email": ("e-posta", "eposta", "email", "mail", "e posta"),
    "unvan": ("unvan", "ünvan", "görev unvanı", "gorev unvani"),
    "birim": ("birim",),
    "ust_birim": ("üst birim", "ust birim", "ust_birim", "üst_birim"),
    "role": ("rol", "role"),
    "yonetici_sicil": (
        "yönetici sicil",
        "yonetici sicil",
        "yonetici_sicil",
        "1. amir sicil",
        "1 amir sicil",
        "birinci amir sicil",
        "1. yönetici sicil",
        "1 yonetici sicil",
        "birinci yönetici sicil",
        "1. amir",
        "1 amir",
        "birinci amir",
        "new_y1",
        "old_y1",
    ),
    "ikinci_yonetici_sicil": (
        "ikinci yönetici sicil",
        "ikinci yonetici sicil",
        "ikinci_yonetici_sicil",
        "2. amir sicil",
        "2 amir sicil",
        "ikinci amir sicil",
        "2. yönetici sicil",
        "2 yonetici sicil",
        "ikinci yönetici sicil",
        "2. amir",
        "2 amir",
        "ikinci amir",
        "new_y2",
        "old_y2",
    ),
    "ucuncu_yonetici_sicil": (
        "üçüncü yönetici sicil",
        "ucuncu yonetici sicil",
        "ucuncu_yonetici_sicil",
        "3. amir sicil",
        "3 amir sicil",
        "üçüncü amir sicil",
        "ucuncu amir sicil",
        "3. yönetici sicil",
        "3 yonetici sicil",
        "üçüncü yönetici sicil",
        "3. amir",
        "3 amir",
        "üçüncü amir",
        "ucuncu amir",
        "new_y3",
        "old_y3",
        "y3",
    ),
    "is_active": ("is_active", "aktif", "durum"),
}


@dataclass(slots=True)
class PersonnelPayload:
    ad: str
    soyad: str
    sicil_no: str
    email: str
    unvan: str
    role: str
    role_label: str
    birim: str
    ust_birim: str
    yonetici_sicil: str | None
    ikinci_yonetici_sicil: str | None
    ucuncu_yonetici_sicil: str | None
    is_active: bool

    @property
    def manager_values(self) -> list[str]:
        return [
            value
            for value in [
                self.yonetici_sicil,
                self.ikinci_yonetici_sicil,
                self.ucuncu_yonetici_sicil,
            ]
            if value
        ]


@dataclass(slots=True)
class ExcelImportSummary:
    created_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    skipped_admin_count: int = 0


def _normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = text.replace("ı", "i").replace("İ", "i")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.replace("_", " ").strip().lower().split())


def canonical_role_value(raw_role: Any) -> str:
    normalized = _normalize_text(raw_role)
    if not normalized:
        return "personel"
    return ROLE_VALUE_BY_NORMALIZED.get(normalized, normalized.replace(" ", "_"))


def canonical_role_label(raw_role: Any) -> str:
    role_value = canonical_role_value(raw_role)
    return ROLE_LABEL_BY_VALUE.get(role_value, str(raw_role or "Personel").strip() or "Personel")


def get_role_choices() -> list[tuple[str, str]]:
    return list(ROLE_CHOICES)


def build_personnel_form_context(*, exclude_user_id: int | None = None) -> dict[str, Any]:
    manager_query = User.query.filter(User.role != "admin", User.is_active == True)
    if exclude_user_id:
        manager_query = manager_query.filter(User.id != exclude_user_id)

    manager_candidates = (
        manager_query
        .order_by(User.ust_birim.asc(), User.birim.asc(), User.ad.asc(), User.soyad.asc())
        .all()
    )

    units = (
        OrganizationUnit.query
        .filter(OrganizationUnit.is_active == True)
        .order_by(OrganizationUnit.sort_order.asc(), OrganizationUnit.name.asc(), OrganizationUnit.id.asc())
        .all()
    )

    org_units: list[dict[str, Any]] = []
    unit_name_values = set()
    parent_name_values = set()
    for unit in units:
        parent_name = unit.parent.name if getattr(unit, "parent", None) else unit.name
        label = unit.name
        if getattr(unit, "parent", None):
            label = f"{unit.parent.name} / {unit.name}"
        org_units.append(
            {
                "id": unit.id,
                "name": unit.name,
                "parent_name": parent_name,
                "label": label,
                "unit_type": unit.unit_type,
            }
        )
        if unit.name:
            unit_name_values.add(unit.name)
        if parent_name:
            parent_name_values.add(parent_name)

    for value, in (
        db.session.query(User.birim)
        .filter(User.birim.isnot(None), User.birim != "")
        .distinct()
        .all()
    ):
        if value:
            unit_name_values.add(value)

    for value, in (
        db.session.query(User.ust_birim)
        .filter(User.ust_birim.isnot(None), User.ust_birim != "")
        .distinct()
        .all()
    ):
        if value:
            parent_name_values.add(value)

    return {
        "role_choices": get_role_choices(),
        "role_values": [label for _, label in ROLE_CHOICES],
        "org_units": org_units,
        "unit_name_options": sorted(unit_name_values),
        "parent_unit_options": sorted(parent_name_values),
        "manager_candidates": manager_candidates,
        "managers": manager_candidates,
    }


def build_payload_from_personnel_form(form, *, current_role: str | None = None) -> PersonnelPayload:
    raw_role = (form.get("role") or current_role or "personel").strip()
    role_value = canonical_role_value(raw_role)
    role_label = canonical_role_label(raw_role)
    return PersonnelPayload(
        ad=(form.get("ad") or "").strip(),
        soyad=(form.get("soyad") or "").strip(),
        sicil_no=(form.get("sicil_no") or "").strip(),
        email=(form.get("email") or "").strip().lower(),
        unvan=(form.get("unvan") or "").strip(),
        role=role_value,
        role_label=role_label,
        birim=(form.get("birim") or "").strip(),
        ust_birim=(form.get("ust_birim") or "").strip(),
        yonetici_sicil=((form.get("yonetici_sicil") or "").strip() or None),
        ikinci_yonetici_sicil=((form.get("ikinci_yonetici_sicil") or "").strip() or None),
        ucuncu_yonetici_sicil=((form.get("ucuncu_yonetici_sicil") or "").strip() or None),
        is_active=bool_from_form(form.get("is_active")),
    )


def build_excel_header_map(raw_headers: list[Any]) -> dict[str, int]:
    normalized_headers = {
        _normalize_text(header): index
        for index, header in enumerate(raw_headers)
        if _normalize_text(header)
    }
    resolved: dict[str, int] = {}
    for key, aliases in EXCEL_HEADER_ALIASES.items():
        for alias in aliases:
            normalized_alias = _normalize_text(alias)
            if normalized_alias in normalized_headers:
                resolved[key] = normalized_headers[normalized_alias]
                break
    return resolved


def get_excel_required_missing(raw_headers: list[Any], required_keys: list[str]) -> list[str]:
    header_map = build_excel_header_map(raw_headers)
    return [key for key in required_keys if key not in header_map]


def _normalize_excel_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def get_excel_cell_value(row: tuple[Any, ...], header_map: dict[str, int], key: str, default: str = "") -> str:
    index = header_map.get(key)
    if index is None or index >= len(row):
        return default
    value = row[index]
    normalized = _normalize_excel_scalar(value)
    return normalized if normalized != "" else default


def build_payload_from_excel_row(
    row: tuple[Any, ...],
    header_map: dict[str, int],
    *,
    activate_new_users: bool,
) -> PersonnelPayload:
    raw_role = get_excel_cell_value(row, header_map, "role", "personel")
    birim = get_excel_cell_value(row, header_map, "birim")
    ust_birim = get_excel_cell_value(row, header_map, "ust_birim") or birim
    is_active_raw = get_excel_cell_value(row, header_map, "is_active", "1")
    is_active = bool_from_form(is_active_raw)
    if not is_active_raw.strip():
        is_active = activate_new_users

    return PersonnelPayload(
        ad=get_excel_cell_value(row, header_map, "ad"),
        soyad=get_excel_cell_value(row, header_map, "soyad"),
        sicil_no=get_excel_cell_value(row, header_map, "sicil_no"),
        email=get_excel_cell_value(row, header_map, "email").lower(),
        unvan=get_excel_cell_value(row, header_map, "unvan"),
        role=canonical_role_value(raw_role),
        role_label=canonical_role_label(raw_role),
        birim=birim,
        ust_birim=ust_birim,
        yonetici_sicil=(get_excel_cell_value(row, header_map, "yonetici_sicil") or None),
        ikinci_yonetici_sicil=(get_excel_cell_value(row, header_map, "ikinci_yonetici_sicil") or None),
        ucuncu_yonetici_sicil=(get_excel_cell_value(row, header_map, "ucuncu_yonetici_sicil") or None),
        is_active=is_active,
    )


def resolve_manager_sicils_from_ids(
    manager_1_id: int | None,
    manager_2_id: int | None,
    manager_3_id: int | None,
) -> tuple[str | None, str | None, str | None]:
    ids = [manager_id for manager_id in [manager_1_id, manager_2_id, manager_3_id] if manager_id]
    if not ids:
        return None, None, None
    managers = User.query.filter(User.id.in_(ids)).all()
    by_id = {manager.id: (manager.sicil_no or "").strip() or None for manager in managers}
    return by_id.get(manager_1_id), by_id.get(manager_2_id), by_id.get(manager_3_id)


def resolve_manager_ids_for_user(user: User) -> tuple[int | None, int | None, int | None]:
    sicil_values = [
        (getattr(user, "yonetici_sicil", None) or "").strip() or None,
        (getattr(user, "ikinci_yonetici_sicil", None) or "").strip() or None,
        (getattr(user, "ucuncu_yonetici_sicil", None) or "").strip() or None,
    ]
    query_values = [value for value in sicil_values if value]
    if not query_values:
        return None, None, None
    managers = User.query.filter(User.sicil_no.in_(query_values)).all()
    by_sicil = {manager.sicil_no: manager.id for manager in managers if manager.sicil_no}
    return tuple(by_sicil.get(value) for value in sicil_values)  # type: ignore[return-value]


def validate_personnel_payload(
    payload: PersonnelPayload,
    *,
    current_user_id: int | None = None,
) -> tuple[str, str] | None:
    if not payload.ad or not payload.soyad or not payload.sicil_no or not payload.email or not payload.unvan or not payload.birim:
        return "Ad, soyad, sicil no, e-posta, unvan ve birim alanları zorunludur.", "warning"

    sicil_query = User.query.filter(User.sicil_no == payload.sicil_no)
    email_query = User.query.filter(User.email == payload.email)
    if current_user_id:
        sicil_query = sicil_query.filter(User.id != current_user_id)
        email_query = email_query.filter(User.id != current_user_id)

    if sicil_query.first():
        return "Bu sicil numarası başka bir kullanıcıda kayıtlı." if current_user_id else "Bu sicil numarası zaten kayıtlı.", "danger"

    if email_query.first():
        return "Bu e-posta adresi başka bir kullanıcıda kayıtlı." if current_user_id else "Bu e-posta adresi zaten kayıtlı.", "danger"

    if not is_allowed_corporate_email(payload.email):
        return corporate_email_error_message(), "warning"

    if payload.sicil_no in payload.manager_values:
        return "Personel kendisini amir olarak seçemez.", "warning"

    if len(payload.manager_values) != len(set(payload.manager_values)):
        return "Aynı kişi birden fazla amir seviyesinde seçilemez.", "warning"

    return None


def apply_personnel_payload(user: User, payload: PersonnelPayload, *, organization_unit_id: int | None) -> None:
    user.ad = payload.ad
    user.soyad = payload.soyad
    user.sicil_no = payload.sicil_no
    user.email = payload.email
    user.unvan = payload.unvan
    user.role = payload.role
    if hasattr(user, "role_label"):
        user.role_label = payload.role_label
    if hasattr(user, "organization_unit_id"):
        user.organization_unit_id = organization_unit_id
    user.birim = payload.birim
    user.ust_birim = payload.ust_birim
    user.yonetici_sicil = payload.yonetici_sicil
    user.ikinci_yonetici_sicil = payload.ikinci_yonetici_sicil
    user.ucuncu_yonetici_sicil = payload.ucuncu_yonetici_sicil
    user.is_active = payload.is_active
    if hasattr(user, "full_name_cache"):
        user.full_name_cache = f"{payload.ad} {payload.soyad}".strip()


def find_existing_user_for_payload(payload: PersonnelPayload) -> User | None:
    user = User.query.filter(User.sicil_no == payload.sicil_no).first()
    if user:
        return user
    return User.query.filter(User.email == payload.email).first()
