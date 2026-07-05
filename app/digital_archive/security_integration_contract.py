"""BYS360 Dijital Arşiv güvenlik entegrasyon sözleşmesi.

DA-9C aşaması POST açmaz ve DB yazmaz.
Bu modül yalnızca Dijital Arşiv yazma akışları açılmadan önce uygulanacak
login, yetki, CSRF, validation, whitelist, audit ve transaction sırasını tanımlar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.digital_archive.security_contract import (
    digital_archive_write_is_enabled,
    get_digital_archive_write_operations,
)


DIGITAL_ARCHIVE_SECURITY_CONTRACT_VERSION = "DA-9C"
DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED = False


@dataclass(frozen=True)
class DigitalArchiveSecurityRequirement:
    """Dijital Arşiv güvenlik entegrasyon gereksinimi."""

    key: str
    title: str
    mandatory: bool
    candidate_modules: tuple[str, ...]
    implementation_note: str


@dataclass(frozen=True)
class DigitalArchiveOperationSecurityProfile:
    """Operasyon bazlı güvenlik profili."""

    operation_key: str
    table_name: str
    draft_route: str
    required_permission: str
    audit_action: str
    authentication_required: bool = True
    route_permission_required: bool = True
    csrf_required: bool = True
    payload_validation_required: bool = True
    field_whitelist_required: bool = True
    audit_required: bool = True
    transaction_required: bool = True
    feature_flag_guard_required: bool = True


DIGITAL_ARCHIVE_INTEGRATION_CANDIDATES: Mapping[str, tuple[str, ...]] = {
    "authentication": (
        "app/account/routes.py",
        "app/admin/ai_phase11_routes.py",
        "app/admin/ai_routes.py",
    ),
    "permission": (
        "app/file_center/services.py",
        "app/portal/routes.py",
        "app/security/decorators.py",
    ),
    "csrf": (
        "app/extensions.py",
        "app/error_handlers.py",
        "app/security/audit.py",
        "app/communication/announcement_popup_routes.py",
    ),
    "audit": (
        "app/security_audit.py",
        "app/security/audit.py",
        "app/file_center/routes.py",
        "app/bootstrap/operational_guards.py",
    ),
    "transaction_example": (
        "app/admin/routes.py",
        "app/admin/ops_user_action_services.py",
        "app/communication/messages_routes.py",
    ),
}


DIGITAL_ARCHIVE_SECURITY_REQUIREMENTS: Mapping[str, DigitalArchiveSecurityRequirement] = {
    "authentication": DigitalArchiveSecurityRequirement(
        key="authentication",
        title="Oturum doğrulaması",
        mandatory=True,
        candidate_modules=DIGITAL_ARCHIVE_INTEGRATION_CANDIDATES["authentication"],
        implementation_note="Tüm yazma akışları mevcut BYS360 oturum kontrolü arkasında çalışmalıdır.",
    ),
    "route_permission": DigitalArchiveSecurityRequirement(
        key="route_permission",
        title="Route seviyesinde yetki kontrolü",
        mandatory=True,
        candidate_modules=DIGITAL_ARCHIVE_INTEGRATION_CANDIDATES["permission"],
        implementation_note="Her operasyon kendi required_permission değeri ile kontrol edilmelidir.",
    ),
    "csrf": DigitalArchiveSecurityRequirement(
        key="csrf",
        title="CSRF doğrulaması",
        mandatory=True,
        candidate_modules=DIGITAL_ARCHIVE_INTEGRATION_CANDIDATES["csrf"],
        implementation_note="Form gönderimleri mevcut BYS360 CSRF omurgasından geçirilmelidir.",
    ),
    "payload_validation": DigitalArchiveSecurityRequirement(
        key="payload_validation",
        title="Sunucu tarafı validasyon",
        mandatory=True,
        candidate_modules=("app/digital_archive/validation_contract.py",),
        implementation_note="Payload önce DA-8A validasyon sözleşmesinden geçmelidir.",
    ),
    "field_whitelist": DigitalArchiveSecurityRequirement(
        key="field_whitelist",
        title="Alan whitelist kontrolü",
        mandatory=True,
        candidate_modules=("app/digital_archive/security_contract.py",),
        implementation_note="Whitelist dışı alanlar yazma akışına alınmamalıdır.",
    ),
    "audit_event": DigitalArchiveSecurityRequirement(
        key="audit_event",
        title="Audit ve güvenlik izi",
        mandatory=True,
        candidate_modules=DIGITAL_ARCHIVE_INTEGRATION_CANDIDATES["audit"],
        implementation_note="Başarılı, başarısız ve reddedilen kritik işlemler iz bırakmalıdır.",
    ),
    "transaction": DigitalArchiveSecurityRequirement(
        key="transaction",
        title="Transaction sınırı",
        mandatory=True,
        candidate_modules=DIGITAL_ARCHIVE_INTEGRATION_CANDIDATES["transaction_example"],
        implementation_note="Yazma akışında hata olduğunda işlem güvenli biçimde geri alınmalıdır.",
    ),
    "feature_flag": DigitalArchiveSecurityRequirement(
        key="feature_flag",
        title="Feature flag kapısı",
        mandatory=True,
        candidate_modules=("app/digital_archive/security_contract.py",),
        implementation_note="Yazma davranışı açıkça izin verilmeden aktif olmamalıdır.",
    ),
    "failure_handling": DigitalArchiveSecurityRequirement(
        key="failure_handling",
        title="Hata yönetimi",
        mandatory=True,
        candidate_modules=("app/error_handlers.py",),
        implementation_note="Yetki, CSRF, validation ve kayıt hataları kullanıcıya güvenli mesajla dönmelidir.",
    ),
}


DIGITAL_ARCHIVE_SECURITY_DECISION_ORDER: tuple[str, ...] = (
    "authentication",
    "route_permission",
    "csrf",
    "feature_flag",
    "field_whitelist",
    "payload_validation",
    "transaction",
    "audit_event",
    "failure_handling",
)


def _build_operation_security_profiles() -> dict[str, DigitalArchiveOperationSecurityProfile]:
    profiles: dict[str, DigitalArchiveOperationSecurityProfile] = {}

    for operation_key, operation in get_digital_archive_write_operations().items():
        profiles[operation_key] = DigitalArchiveOperationSecurityProfile(
            operation_key=operation_key,
            table_name=operation.table_name,
            draft_route=operation.draft_route,
            required_permission=operation.required_permission,
            audit_action=operation.audit_action,
            csrf_required=operation.csrf_required,
            payload_validation_required=True,
            field_whitelist_required=operation.whitelist_required,
            transaction_required=operation.transaction_required,
        )

    return profiles


DIGITAL_ARCHIVE_OPERATION_SECURITY_PROFILES: Mapping[str, DigitalArchiveOperationSecurityProfile] = (
    _build_operation_security_profiles()
)


def digital_archive_security_integration_is_enabled() -> bool:
    """DA-9C aşamasında güvenlik entegrasyonu aktif yazma davranışı açmaz."""

    return DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED


def digital_archive_security_contract_allows_write() -> bool:
    """Yazma izni yalnızca ana yazma bayrağı açıldığında mümkün olabilir."""

    return bool(digital_archive_write_is_enabled() and DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED)


def get_digital_archive_security_requirements() -> Mapping[str, DigitalArchiveSecurityRequirement]:
    """Güvenlik entegrasyon gereksinimlerini döndürür."""

    return DIGITAL_ARCHIVE_SECURITY_REQUIREMENTS


def get_digital_archive_security_decision_order() -> tuple[str, ...]:
    """Yazma açıldığında uygulanacak güvenlik karar sırasını döndürür."""

    return DIGITAL_ARCHIVE_SECURITY_DECISION_ORDER


def get_digital_archive_operation_security_profiles() -> Mapping[str, DigitalArchiveOperationSecurityProfile]:
    """Operasyon bazlı güvenlik profillerini döndürür."""

    return DIGITAL_ARCHIVE_OPERATION_SECURITY_PROFILES


def get_digital_archive_operation_security_profile(
    operation_key: str,
) -> DigitalArchiveOperationSecurityProfile | None:
    """Tek operasyon için güvenlik profilini döndürür."""

    return DIGITAL_ARCHIVE_OPERATION_SECURITY_PROFILES.get(operation_key)


def get_digital_archive_integration_candidate_modules() -> Mapping[str, tuple[str, ...]]:
    """DA-9A/DA-9B keşiflerinden çıkan örnek entegrasyon adaylarını döndürür."""

    return DIGITAL_ARCHIVE_INTEGRATION_CANDIDATES
