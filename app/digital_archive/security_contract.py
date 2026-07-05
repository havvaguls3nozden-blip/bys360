"""BYS360 Dijital Arşiv yazma güvenliği mimari sözleşmesi.

DA-6B aşaması veri yazma açmaz.
Bu modül yalnızca ileride açılacak yazma işlemleri için güvenlik sözleşmesini
kod seviyesinde tanımlar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


DIGITAL_ARCHIVE_WRITE_ENABLED = False


@dataclass(frozen=True)
class DigitalArchiveWriteOperation:
    """Dijital Arşiv için ileride açılabilecek güvenli yazma operasyonu."""

    key: str
    table_name: str
    draft_route: str
    required_permission: str
    audit_action: str
    csrf_required: bool = True
    transaction_required: bool = True
    whitelist_required: bool = True
    soft_delete_required: bool = True


DIGITAL_ARCHIVE_WRITE_OPERATIONS: Mapping[str, DigitalArchiveWriteOperation] = {
    "category_create": DigitalArchiveWriteOperation(
        key="category_create",
        table_name="digital_archive_categories",
        draft_route="/digital-archive/categories/new",
        required_permission="digital_archive.category.create",
        audit_action="digital_archive.category.create",
    ),
    "physical_location_create": DigitalArchiveWriteOperation(
        key="physical_location_create",
        table_name="digital_archive_physical_locations",
        draft_route="/digital-archive/physical-locations/new",
        required_permission="digital_archive.physical_location.create",
        audit_action="digital_archive.physical_location.create",
    ),
    "retention_policy_create": DigitalArchiveWriteOperation(
        key="retention_policy_create",
        table_name="digital_archive_retention_policies",
        draft_route="/digital-archive/retention-policies/new",
        required_permission="digital_archive.retention_policy.create",
        audit_action="digital_archive.retention_policy.create",
    ),
}


DIGITAL_ARCHIVE_FIELD_WHITELISTS: Mapping[str, tuple[str, ...]] = {
    "category_create": (
        "code",
        "name",
        "title",
        "description",
        "is_active",
    ),
    "physical_location_create": (
        "code",
        "name",
        "building",
        "room",
        "shelf",
        "box",
        "description",
        "is_active",
    ),
    "retention_policy_create": (
        "code",
        "name",
        "retention_years",
        "action",
        "description",
        "is_active",
    ),
}


DIGITAL_ARCHIVE_WRITE_SECURITY_REQUIREMENTS: tuple[str, ...] = (
    "route_level_permission_check",
    "csrf_validation",
    "server_side_validation",
    "field_whitelist",
    "audit_event",
    "transaction_rollback",
    "soft_delete_policy",
    "pre_deploy_backup",
)


def digital_archive_write_is_enabled() -> bool:
    """DA-6B aşamasında yazma kapalıdır."""

    return DIGITAL_ARCHIVE_WRITE_ENABLED


def get_digital_archive_write_operations() -> Mapping[str, DigitalArchiveWriteOperation]:
    """Tanımlı yazma operasyon sözleşmelerini döndürür."""

    return DIGITAL_ARCHIVE_WRITE_OPERATIONS


def get_digital_archive_field_whitelist(operation_key: str) -> tuple[str, ...]:
    """Operasyon bazlı güvenli alan listesini döndürür."""

    return DIGITAL_ARCHIVE_FIELD_WHITELISTS.get(operation_key, ())


def get_digital_archive_write_security_requirements() -> tuple[str, ...]:
    """Yazma açılmadan önce zorunlu güvenlik gereksinimlerini döndürür."""

    return DIGITAL_ARCHIVE_WRITE_SECURITY_REQUIREMENTS
