
"""Personel form payload okuma yardımcıları.

Canlı sağlamlaştırma notu:
- Personel kategori alanı korunur.
- PERSONNEL_MANAGER_FIELDS ve doğrulama exportları geri yüklenir.
- Bu dosya veritabanına yazmaz; yalnızca form payload okur/doğrular.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from collections.abc import Mapping

try:
    from .categories import normalize_personnel_category_label
except Exception:  # pragma: no cover - canlı import güvenliği
    def normalize_personnel_category_label(value: Any) -> str:
        text = str(value or "").strip()
        return text or "Diğer"


PERSONNEL_REQUIRED_FIELDS: tuple[str, ...] = (
    "ad",
    "soyad",
    "sicil_no",
    "email",
    "unvan",
    "birim",
    "ust_birim",
)

PERSONNEL_MANAGER_FIELDS: tuple[str, ...] = (
    "manager_1_id",
    "manager_2_id",
    "manager_3_id",
)

# BYS360_PERSONNEL_CATEGORY_PAYLOAD_FIELD


@dataclass(frozen=True, slots=True)
class PersonnelFormPayload:
    ad: str = ""
    soyad: str = ""
    sicil_no: str = ""
    email: str = ""
    unvan: str = ""
    role_value: str = ""
    personnel_category: str = "Diğer"
    birim: str = ""
    ust_birim: str = ""
    manager_1_id: int | None = None
    manager_2_id: int | None = None
    manager_3_id: int | None = None
    is_active: bool | None = None
    must_change_password: bool | None = None
    must_set_security_question: bool | None = None
    new_password: str = ""
    new_password_repeat: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.ad} {self.soyad}".strip()

    @property
    def manager_ids(self) -> list[int]:
        return [value for value in (self.manager_1_id, self.manager_2_id, self.manager_3_id) if value]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_template_defaults(self) -> dict[str, Any]:
        data = self.to_dict()
        data["role"] = data.pop("role_value")
        return data


@dataclass(frozen=True, slots=True)
class PersonnelFormValidationResult:
    ok: bool
    errors: tuple[str, ...]
    missing_fields: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _form_get(form: Mapping[str, Any], key: str, default: Any = "") -> Any:
    getter = getattr(form, "get", None)
    if callable(getter):
        return getter(key, default)
    return form[key] if key in form else default


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_email(value: Any) -> str:
    return _clean_text(value).lower()


def _clean_int(value: Any) -> int | None:
    if value is None:
        return None
    text = _clean_text(value)
    if not text:
        return None
    try:
        parsed = int(text)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _clean_personnel_category(value: Any) -> str:
    return normalize_personnel_category_label(value)


def _clean_bool(value: Any) -> bool | None:
    if value is None:
        return None
    text = _clean_text(value).lower()
    if text in {"1", "true", "on", "yes", "evet", "aktif"}:
        return True
    if text in {"0", "false", "off", "no", "hayir", "hayır", "pasif"}:
        return False
    return None


def read_personnel_form_payload(form: Mapping[str, Any], *, include_password_fields: bool = False) -> PersonnelFormPayload:
    """Read personnel form fields without mutating models or DB state."""
    new_password = _clean_text(_form_get(form, "new_password")) if include_password_fields else ""
    new_password_repeat = _clean_text(_form_get(form, "new_password_repeat")) if include_password_fields else ""
    return PersonnelFormPayload(
        ad=_clean_text(_form_get(form, "ad")),
        soyad=_clean_text(_form_get(form, "soyad")),
        sicil_no=_clean_text(_form_get(form, "sicil_no")),
        email=_clean_email(_form_get(form, "email")),
        unvan=_clean_text(_form_get(form, "unvan")),
        role_value=_clean_text(_form_get(form, "role")),
        personnel_category=_clean_personnel_category(_form_get(form, "personnel_category", "Diğer")),
        birim=_clean_text(_form_get(form, "birim")),
        ust_birim=_clean_text(_form_get(form, "ust_birim")),
        manager_1_id=_clean_int(_form_get(form, "manager_1_id")),
        manager_2_id=_clean_int(_form_get(form, "manager_2_id")),
        manager_3_id=_clean_int(_form_get(form, "manager_3_id")),
        is_active=_clean_bool(_form_get(form, "is_active", None)),
        must_change_password=_clean_bool(_form_get(form, "must_change_password", None)),
        must_set_security_question=_clean_bool(_form_get(form, "must_set_security_question", None)),
        new_password=new_password,
        new_password_repeat=new_password_repeat,
    )


def missing_required_personnel_fields(payload: PersonnelFormPayload) -> tuple[str, ...]:
    missing = [field for field in PERSONNEL_REQUIRED_FIELDS if not getattr(payload, field, "")]
    return tuple(missing)


def validate_required_personnel_payload(payload: PersonnelFormPayload) -> PersonnelFormValidationResult:
    missing = missing_required_personnel_fields(payload)
    if missing:
        return PersonnelFormValidationResult(
            ok=False,
            errors=("required_fields_missing",),
            missing_fields=missing,
        )
    return PersonnelFormValidationResult(ok=True, errors=())


def validate_manager_selection(*, current_user_id: int | None, manager_ids: list[int]) -> PersonnelFormValidationResult:
    clean_ids = [int(value) for value in manager_ids if value]
    errors: list[str] = []
    if current_user_id and int(current_user_id) in clean_ids:
        errors.append("self_manager_not_allowed")
    if len(clean_ids) != len(set(clean_ids)):
        errors.append("duplicate_manager_not_allowed")
    return PersonnelFormValidationResult(ok=not errors, errors=tuple(errors))


def validate_edit_password_fields(new_password: str, new_password_repeat: str) -> PersonnelFormValidationResult:
    if not new_password and not new_password_repeat:
        return PersonnelFormValidationResult(ok=True, errors=())
    errors: list[str] = []
    if len(new_password) < 8:
        errors.append("password_min_length")
    if new_password != new_password_repeat:
        errors.append("password_repeat_mismatch")
    return PersonnelFormValidationResult(ok=not errors, errors=tuple(errors))
