"""BYS360 Dijital Arşiv write service dry-run sözleşmesi.

DA-10B aşaması gerçek yazma yapmaz.
Bu servis yalnızca payload -> whitelist -> validation -> security guard akışını
bellekte doğrular.

POST route açılmaz.
DB session kullanılmaz.
Commit / flush / merge / delete yapılmaz.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from app.digital_archive.security_contract import (
    get_digital_archive_field_whitelist,
    get_digital_archive_write_operations,
)
from app.digital_archive.security_integration_contract import (
    digital_archive_security_contract_allows_write,
    get_digital_archive_operation_security_profile,
)
from app.digital_archive.validation_contract import validate_digital_archive_payload


DIGITAL_ARCHIVE_WRITE_SERVICE_MODE = "DRY_RUN"
DIGITAL_ARCHIVE_WRITE_SERVICE_VERSION = "DA-10B"


@dataclass(frozen=True)
class DigitalArchiveWriteIntent:
    """DB yazmadan oluşturulan yazma niyeti."""

    operation_key: str
    table_name: str
    draft_route: str
    raw_keys: tuple[str, ...]
    accepted_fields: tuple[str, ...]
    rejected_fields: tuple[str, ...]
    payload: Mapping[str, Any]
    is_valid: bool
    validation_errors: tuple[str, ...]
    write_allowed: bool
    guard_reasons: tuple[str, ...]


def _as_error_tuple(errors: Any) -> tuple[str, ...]:
    if errors is None:
        return ()

    if isinstance(errors, Mapping):
        return tuple(f"{key}: {value}" for key, value in errors.items())

    if isinstance(errors, (list, tuple, set)):
        return tuple(str(item) for item in errors)

    return (str(errors),)


def build_digital_archive_write_intent(
    operation_key: str,
    raw_payload: Mapping[str, Any] | None,
    *,
    user_id: int | None = None,
) -> DigitalArchiveWriteIntent:
    """Yazma operasyonu için DB yazmadan güvenli niyet üretir."""

    del user_id

    operations = get_digital_archive_write_operations()
    operation = operations.get(operation_key)
    profile = get_digital_archive_operation_security_profile(operation_key)

    safe_payload: Mapping[str, Any] = raw_payload or {}
    raw_keys = tuple(sorted(str(key) for key in safe_payload.keys()))

    if operation is None or profile is None:
        return DigitalArchiveWriteIntent(
            operation_key=operation_key,
            table_name="",
            draft_route="",
            raw_keys=raw_keys,
            accepted_fields=(),
            rejected_fields=raw_keys,
            payload={},
            is_valid=False,
            validation_errors=("unknown_operation",),
            write_allowed=False,
            guard_reasons=("unknown_operation", "write_disabled"),
        )

    whitelist = tuple(get_digital_archive_field_whitelist(operation_key))
    whitelist_set = set(whitelist)

    normalized_payload = {
        key: value
        for key, value in safe_payload.items()
        if str(key) in whitelist_set
    }

    accepted_fields = tuple(sorted(str(key) for key in normalized_payload.keys()))
    rejected_fields = tuple(sorted(set(raw_keys) - set(accepted_fields)))

    validation_result = validate_digital_archive_payload(operation_key, normalized_payload)
    validation_errors = _as_error_tuple(getattr(validation_result, "errors", ()))
    is_valid = bool(getattr(validation_result, "is_valid", False))

    guard_reasons: list[str] = []

    if not is_valid:
        guard_reasons.append("validation_failed")

    if not digital_archive_security_contract_allows_write():
        guard_reasons.append("write_disabled")

    write_allowed = bool(is_valid and not guard_reasons)

    return DigitalArchiveWriteIntent(
        operation_key=operation_key,
        table_name=operation.table_name,
        draft_route=operation.draft_route,
        raw_keys=raw_keys,
        accepted_fields=accepted_fields,
        rejected_fields=rejected_fields,
        payload=normalized_payload,
        is_valid=is_valid,
        validation_errors=validation_errors,
        write_allowed=write_allowed,
        guard_reasons=tuple(guard_reasons),
    )
