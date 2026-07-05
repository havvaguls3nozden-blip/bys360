"""BYS360 Dijital Arşiv server-side validation sözleşmesi.

DA-8A aşaması POST açmaz ve DB yazmaz.
Bu modül yalnızca ileride açılacak yazma işlemleri için saf validasyon
kurallarını tanımlar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.digital_archive.security_contract import get_digital_archive_field_whitelist


@dataclass(frozen=True)
class DigitalArchiveValidationResult:
    """Saf validasyon sonucu."""

    is_valid: bool
    errors: tuple[str, ...]
    cleaned_data: Mapping[str, Any]


DIGITAL_ARCHIVE_REQUIRED_FIELDS: Mapping[str, tuple[str, ...]] = {
    "category_create": (
        "name",
    ),
    "physical_location_create": (
        "archive_room",
    ),
    "retention_policy_create": (
        "name",
        "retention_years",
        "action",
    ),
}


DIGITAL_ARCHIVE_MAX_LENGTHS: Mapping[str, Mapping[str, int]] = {
    "category_create": {
        "code": 64,
        "name": 255,
        "description": 2000,
    },
    "physical_location_create": {
        "archive_room": 255,
        "cabinet_no": 64,
        "shelf_no": 64,
        "box_no": 64,
        "folder_no": 64,
        "file_no": 64,
        "physical_status": 64,
    },
    "retention_policy_create": {
        "name": 255,
        "action": 64,
        "description": 2000,
    },
}


DIGITAL_ARCHIVE_BOOLEAN_FIELDS: Mapping[str, tuple[str, ...]] = {
    "category_create": (
        "is_active",
    ),
    "physical_location_create": (),
    "retention_policy_create": (
        "requires_approval",
        "is_active",
    ),
}


DIGITAL_ARCHIVE_INTEGER_FIELDS: Mapping[str, tuple[str, ...]] = {
    "category_create": (
        "parent_id",
        "sort_order",
    ),
    "physical_location_create": (),
    "retention_policy_create": (
        "retention_years",
    ),
}


def _clean_string(value: Any) -> str:
    return str(value).strip()


def _clean_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None

    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()

    if normalized in {"1", "true", "yes", "on", "evet", "aktif"}:
        return True

    if normalized in {"0", "false", "no", "off", "hayır", "hayir", "pasif"}:
        return False

    raise ValueError("Geçerli boolean değer değil.")


def _clean_int(value: Any) -> int | None:
    if value is None or value == "":
        return None

    return int(str(value).strip())


def validate_digital_archive_payload(
    operation_key: str,
    payload: Mapping[str, Any],
) -> DigitalArchiveValidationResult:
    """Operasyon bazlı saf validasyon uygular.

    Bu fonksiyon DB yazmaz, request objesine erişmez ve commit/rollback yapmaz.
    """

    whitelist = tuple(get_digital_archive_field_whitelist(operation_key))
    required_fields = DIGITAL_ARCHIVE_REQUIRED_FIELDS.get(operation_key, ())
    max_lengths = DIGITAL_ARCHIVE_MAX_LENGTHS.get(operation_key, {})
    boolean_fields = set(DIGITAL_ARCHIVE_BOOLEAN_FIELDS.get(operation_key, ()))
    integer_fields = set(DIGITAL_ARCHIVE_INTEGER_FIELDS.get(operation_key, ()))

    errors: list[str] = []
    cleaned_data: dict[str, Any] = {}

    if not whitelist:
        errors.append(f"Bilinmeyen operasyon: {operation_key}")
        return DigitalArchiveValidationResult(False, tuple(errors), {})

    unexpected_fields = sorted(set(payload.keys()) - set(whitelist))
    if unexpected_fields:
        errors.append(f"Whitelist dışı alan var: {', '.join(unexpected_fields)}")

    for field in whitelist:
        raw_value = payload.get(field)

        try:
            if field in boolean_fields:
                cleaned_value = _clean_bool(raw_value)
            elif field in integer_fields:
                cleaned_value = _clean_int(raw_value)
            elif raw_value is None:
                cleaned_value = None
            else:
                cleaned_value = _clean_string(raw_value)
        except (TypeError, ValueError):
            errors.append(f"{field} alanı beklenen tipte değil.")
            continue

        if field in required_fields and (cleaned_value is None or cleaned_value == ""):
            errors.append(f"{field} zorunlu alandır.")

        if isinstance(cleaned_value, str):
            max_length = max_lengths.get(field)
            if max_length and len(cleaned_value) > max_length:
                errors.append(f"{field} en fazla {max_length} karakter olabilir.")

        if field == "retention_years" and cleaned_value is not None and cleaned_value < 0:
            errors.append("retention_years negatif olamaz.")

        cleaned_data[field] = cleaned_value

    return DigitalArchiveValidationResult(
        is_valid=not errors,
        errors=tuple(errors),
        cleaned_data=cleaned_data,
    )
