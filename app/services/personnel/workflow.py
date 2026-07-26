# BYS360_CANLI_SAGLAMLASTIRMA_FAZ1_10_WORKFLOW_IMPORT_CONTRACT

"""Personel kayıt ve güncelleme iş akışı servis köprüsü.

Canlı Sağlamlaştırma Faz 1.10:
- Önceki kategori yamaları sırasında küçülmüş workflow.py dosyasının servis export sözleşmesini geri kurar.
- app.services.personnel.__init__ içindeki PersonnelMutationSummary ve iş akışı helper importlarını karşılar.
- Veritabanı commit/rollback çalıştırmaz; sadece verilen User benzeri modeli hazırlar.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

try:
    from .form_payload import PersonnelFormPayload
except (ImportError, AttributeError):  # pragma: no cover - import kırık ortamda güvenli tip yedeği
    @dataclass(frozen=True, slots=True)
    class PersonnelFormPayload:  # type: ignore[no-redef]
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
        new_password: str = ""

try:
    from .categories import assign_user_performance_category
except (ImportError, AttributeError):  # pragma: no cover
    def assign_user_performance_category(user: Any, category_label: Any, *, db_session: Any | None = None) -> str:
        label = str(category_label or "Diğer").strip() or "Diğer"
        if hasattr(user, "personnel_category"):
            user.personnel_category = label
        return label

PasswordHasher = Callable[[str], str]
EnsureUnitExists = Callable[..., Any]

try:
    from app.security import get_default_first_login_password
except (ImportError, AttributeError):  # pragma: no cover
    def get_default_first_login_password() -> str:
        import secrets
        return secrets.token_urlsafe(12)

@dataclass(frozen=True, slots=True)
class PersonnelMutationSummary:
    phase: str
    mode: str
    db_commit: bool
    db_rollback: bool
    route_contract: str
    photo_handling: str
    password_reset_applied: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _set_if_exists(obj: Any, field_name: str, value: Any) -> None:
    if hasattr(obj, field_name):
        setattr(obj, field_name, value)


def set_personnel_role(user: Any, role_value: str) -> None:
    """role / role_label alanlarını eski-yeni model uyumluluğuyla set eder."""
    if hasattr(user, "role"):
        user.role = role_value
    if hasattr(user, "role_label"):
        user.role_label = role_value


def set_personnel_manager_if_exists(user: Any, field_name: str, value: Any) -> None:
    _set_if_exists(user, field_name, value)


def set_personnel_manager_sicils_from_ids(
    user: Any,
    *,
    user_model: Any,
    db_session: Any,
    manager_1_id: int | None = None,
    manager_2_id: int | None = None,
    manager_3_id: int | None = None,
) -> None:
    """Faz 6 hiyerarşi servisine geriye dönük uyum köprüsü."""
    try:
        from .org_hierarchy import apply_manager_id_hierarchy
    except (ImportError, AttributeError):
        apply_manager_id_hierarchy = None  # type: ignore[assignment]
    if callable(apply_manager_id_hierarchy):
        apply_manager_id_hierarchy(
            user,
            user_model=user_model,
            db_session=db_session,
            manager_1_id=manager_1_id,
            manager_2_id=manager_2_id,
            manager_3_id=manager_3_id,
        )
        return
    # Güvenli yedek: modelde id alanları varsa doğrudan yaz.
    _set_if_exists(user, "manager_1_id", manager_1_id)
    _set_if_exists(user, "manager_2_id", manager_2_id)
    _set_if_exists(user, "manager_3_id", manager_3_id)


def apply_personnel_identity_payload(user: Any, payload: PersonnelFormPayload) -> None:
    """Kimlik/profil alanlarını User benzeri modele uygular."""
    _set_if_exists(user, "ad", getattr(payload, "ad", ""))
    _set_if_exists(user, "soyad", getattr(payload, "soyad", ""))
    _set_if_exists(user, "sicil_no", getattr(payload, "sicil_no", ""))
    _set_if_exists(user, "email", getattr(payload, "email", ""))
    _set_if_exists(user, "unvan", getattr(payload, "unvan", ""))
    _set_if_exists(user, "birim", getattr(payload, "birim", ""))
    _set_if_exists(user, "ust_birim", getattr(payload, "ust_birim", ""))
    _set_if_exists(user, "personnel_category", getattr(payload, "personnel_category", "Diğer") or "Diğer")
    full_name = f"{getattr(payload, 'ad', '')} {getattr(payload, 'soyad', '')}".strip()
    _set_if_exists(user, "full_name_cache", full_name)


def attach_personnel_org_unit(
    user: Any,
    *,
    payload: PersonnelFormPayload,
    ensure_unit_exists: EnsureUnitExists,
    role_for_unit: str,
) -> Any:
    """Organizasyon birimini bağlar; commit/rollback yapmaz."""
    try:
        from .org_hierarchy import attach_organization_unit_to_user
    except (ImportError, AttributeError):
        attach_organization_unit_to_user = None  # type: ignore[assignment]

    if callable(attach_organization_unit_to_user):
        return attach_organization_unit_to_user(
            user,
            birim=getattr(payload, "birim", ""),
            ust_birim=getattr(payload, "ust_birim", ""),
            role=role_for_unit,
            ensure_unit_exists=ensure_unit_exists,
        )

    unit = ensure_unit_exists(
        name=getattr(payload, "birim", ""),
        parent_name=getattr(payload, "ust_birim", ""),
        role=role_for_unit,
    ) if callable(ensure_unit_exists) else None
    if unit is not None and hasattr(user, "organization_unit_id"):
        user.organization_unit_id = getattr(unit, "id", None)
    return unit


def apply_personnel_manager_payload(
    user: Any,
    *,
    payload: PersonnelFormPayload,
    user_model: Any,
    db_session: Any,
) -> None:
    """Payload içindeki 1/2/3. amir id alanlarını uygular."""
    set_personnel_manager_sicils_from_ids(
        user,
        user_model=user_model,
        db_session=db_session,
        manager_1_id=getattr(payload, "manager_1_id", None),
        manager_2_id=getattr(payload, "manager_2_id", None),
        manager_3_id=getattr(payload, "manager_3_id", None),
    )


def apply_personnel_first_login_defaults(user: Any) -> None:
    """İlk giriş bayraklarını eski route davranışıyla uyumlu uygular."""
    _set_if_exists(user, "is_active", True)
    _set_if_exists(user, "must_change_password", True)
    _set_if_exists(user, "must_set_security_question", True)
    _set_if_exists(user, "is_first_login", True)
    _set_if_exists(user, "captcha_required", False)


def apply_personnel_initial_password(
    user: Any,
    *,
    password_hasher: PasswordHasher,
    initial_password: str | None = None,
) -> None:
    """Başlangıç şifresini hashleyerek uygular; commit yapmaz."""
    password_hash = password_hasher(initial_password or get_default_first_login_password())
    if hasattr(user, "password_hash"):
        user.password_hash = password_hash
    elif hasattr(user, "password"):
        user.password = password_hash


def build_new_personnel_user_from_payload(
    *,
    payload: PersonnelFormPayload,
    user_model: Any,
    db_session: Any,
    ensure_unit_exists: EnsureUnitExists,
    password_hasher: PasswordHasher,
    initial_password: str | None = None,
) -> Any:
    """Doğrulanmış payload ile yeni User benzeri nesne oluşturur; session'a eklemez."""
    user = user_model()
    apply_personnel_identity_payload(user, payload)
    assign_user_performance_category(user, getattr(payload, "personnel_category", "Diğer"), db_session=db_session)
    attach_personnel_org_unit(
        user,
        payload=payload,
        ensure_unit_exists=ensure_unit_exists,
        role_for_unit=getattr(payload, "role_value", "") or "personel",
    )
    set_personnel_role(user, getattr(payload, "role_value", "") or "Personel")
    apply_personnel_initial_password(user, password_hasher=password_hasher, initial_password=initial_password)
    apply_personnel_first_login_defaults(user)
    apply_personnel_manager_payload(user, payload=payload, user_model=user_model, db_session=db_session)
    return user


def apply_personnel_edit_flags(
    user: Any,
    *,
    is_active: bool,
    must_change_password: bool,
    must_set_security_question: bool,
) -> None:
    _set_if_exists(user, "is_active", is_active)
    _set_if_exists(user, "must_change_password", must_change_password)
    _set_if_exists(user, "must_set_security_question", must_set_security_question)


def apply_personnel_password_update(
    user: Any,
    *,
    new_password: str,
    password_hasher: PasswordHasher,
) -> bool:
    """Opsiyonel admin şifre sıfırlamasını uygular ve uygulanıp uygulanmadığını döndürür."""
    if not new_password:
        return False
    if hasattr(user, "set_password"):
        user.set_password(new_password)
    else:
        password_hash = password_hasher(new_password)
        if hasattr(user, "password_hash"):
            user.password_hash = password_hash
        elif hasattr(user, "password"):
            user.password = password_hash
    _set_if_exists(user, "must_change_password", True)
    _set_if_exists(user, "must_set_security_question", True)
    return True


def update_existing_personnel_user_from_payload(
    *,
    user: Any,
    payload: PersonnelFormPayload,
    current_role: str,
    user_model: Any,
    db_session: Any,
    ensure_unit_exists: EnsureUnitExists,
    password_hasher: PasswordHasher,
    is_active: bool,
    must_change_password: bool,
    must_set_security_question: bool,
) -> bool:
    """Mevcut User benzeri nesneyi payload ile günceller; commit/rollback yapmaz."""
    attach_personnel_org_unit(
        user,
        payload=payload,
        ensure_unit_exists=ensure_unit_exists,
        role_for_unit=(getattr(payload, "role_value", "") or current_role or "Personel").lower(),
    )
    apply_personnel_identity_payload(user, payload)
    assign_user_performance_category(user, getattr(payload, "personnel_category", "Diğer"), db_session=db_session)
    set_personnel_role(user, getattr(payload, "role_value", "") or current_role or "Personel")
    apply_personnel_edit_flags(
        user,
        is_active=is_active,
        must_change_password=must_change_password,
        must_set_security_question=must_set_security_question,
    )
    apply_personnel_manager_payload(user, payload=payload, user_model=user_model, db_session=db_session)
    return apply_personnel_password_update(
        user,
        new_password=getattr(payload, "new_password", ""),
        password_hasher=password_hasher,
    )


def bind_personnel_category(user: Any, category_label: Any = None, *, db_session: Any | None = None) -> str:
    """Faz 2.2 kategori bağlama helper uyumluluğu."""
    return assign_user_performance_category(user, category_label, db_session=db_session)


def build_personnel_workflow_phase3_summary(*, mode: str, password_reset_applied: bool = False) -> dict[str, Any]:
    return PersonnelMutationSummary(
        phase="personnel_service_faz3",
        mode=mode,
        db_commit=False,
        db_rollback=False,
        route_contract="preserved",
        photo_handling="route_layer_preserved",
        password_reset_applied=password_reset_applied,
    ).to_dict()


__all__ = [
    "PersonnelMutationSummary",
    "apply_personnel_edit_flags",
    "apply_personnel_first_login_defaults",
    "apply_personnel_identity_payload",
    "apply_personnel_initial_password",
    "apply_personnel_manager_payload",
    "apply_personnel_password_update",
    "attach_personnel_org_unit",
    "bind_personnel_category",
    "build_new_personnel_user_from_payload",
    "build_personnel_workflow_phase3_summary",
    "set_personnel_manager_if_exists",
    "set_personnel_manager_sicils_from_ids",
    "set_personnel_role",
    "update_existing_personnel_user_from_payload",
]
