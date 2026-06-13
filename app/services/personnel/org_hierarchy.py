
"""Personel organizasyon birimi ve hiyerarşi atama servis köprüsü.

Faz 6 kapsamı:
- Organizasyon birimi oluşturma/bağlama kararını servis katmanında toplar.
- 1/2/3. amir sicil ve id alanlarının modele yazılmasını tek yerde yönetir.
- Commit/rollback çalıştırmaz; verilen model nesnesini hazırlar.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from .form_payload import PersonnelFormPayload

EnsureUnitExists = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class PersonnelOrgHierarchyResult:
    phase: str
    organization_unit_attached: bool
    manager_level_count: int
    manager_source: str
    db_commit: bool = False
    db_rollback: bool = False
    route_contract: str = "preserved"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _set_if_exists(obj: Any, field_name: str, value: Any) -> None:
    if hasattr(obj, field_name):
        setattr(obj, field_name, value)


def ensure_personnel_organization_unit(
    *,
    birim: str,
    ust_birim: str,
    role: str,
    ensure_unit_exists: EnsureUnitExists,
) -> Any:
    """Resolve/create organization unit through the existing strict helper.

    This function deliberately delegates to the current helper so the live DB
    behaviour is unchanged. It only centralises the call signature.
    """
    return ensure_unit_exists(
        birim_name=(birim or "").strip(),
        ust_birim_name=(ust_birim or "").strip(),
        role=(role or "personel").strip() or "personel",
    )


def attach_organization_unit_to_user(
    user: Any,
    *,
    birim: str,
    ust_birim: str,
    role: str,
    ensure_unit_exists: EnsureUnitExists,
) -> Any:
    """Attach organization unit id and visible unit text fields without commit."""
    org_unit = ensure_personnel_organization_unit(
        birim=birim,
        ust_birim=ust_birim,
        role=role,
        ensure_unit_exists=ensure_unit_exists,
    )
    _set_if_exists(user, "organization_unit_id", org_unit.id if org_unit else None)
    _set_if_exists(user, "birim", (birim or "").strip())
    _set_if_exists(user, "ust_birim", (ust_birim or "").strip())
    return org_unit


def apply_manager_sicil_hierarchy(
    user: Any,
    *,
    yonetici_sicil: str | None = None,
    ikinci_yonetici_sicil: str | None = None,
    ucuncu_yonetici_sicil: str | None = None,
) -> int:
    """Apply 1/2/3 manager sicil fields and return filled level count."""
    values = (
        ("yonetici_sicil", (yonetici_sicil or "").strip() or None),
        ("ikinci_yonetici_sicil", (ikinci_yonetici_sicil or "").strip() or None),
        ("ucuncu_yonetici_sicil", (ucuncu_yonetici_sicil or "").strip() or None),
    )
    count = 0
    for field_name, value in values:
        _set_if_exists(user, field_name, value)
        if value:
            count += 1
    return count


def resolve_manager_by_id(*, user_model: Any, db_session: Any, manager_id: int | None) -> Any:
    if not manager_id:
        return None
    return db_session.get(user_model, manager_id)


def apply_manager_id_hierarchy(
    user: Any,
    *,
    user_model: Any,
    db_session: Any,
    manager_1_id: int | None = None,
    manager_2_id: int | None = None,
    manager_3_id: int | None = None,
) -> int:
    """Apply manager id fields and mirror them to sicil fields without commit."""
    _set_if_exists(user, "manager_1_id", manager_1_id)
    _set_if_exists(user, "manager_2_id", manager_2_id)
    _set_if_exists(user, "manager_3_id", manager_3_id)

    manager_1 = resolve_manager_by_id(user_model=user_model, db_session=db_session, manager_id=manager_1_id)
    manager_2 = resolve_manager_by_id(user_model=user_model, db_session=db_session, manager_id=manager_2_id)
    manager_3 = resolve_manager_by_id(user_model=user_model, db_session=db_session, manager_id=manager_3_id)

    return apply_manager_sicil_hierarchy(
        user,
        yonetici_sicil=getattr(manager_1, "sicil_no", None),
        ikinci_yonetici_sicil=getattr(manager_2, "sicil_no", None),
        ucuncu_yonetici_sicil=getattr(manager_3, "sicil_no", None),
    )


def apply_admin_user_org_hierarchy_fields(
    *,
    user: Any,
    birim: str,
    ust_birim: str,
    role: str,
    yonetici_sicil: str | None,
    ikinci_yonetici_sicil: str | None,
    ucuncu_yonetici_sicil: str | None,
    ensure_unit_exists: EnsureUnitExists,
) -> PersonnelOrgHierarchyResult:
    """Bridge admin user create/edit organization and sicil hierarchy fields."""
    org_unit = attach_organization_unit_to_user(
        user,
        birim=birim,
        ust_birim=ust_birim,
        role=role,
        ensure_unit_exists=ensure_unit_exists,
    )
    manager_count = apply_manager_sicil_hierarchy(
        user,
        yonetici_sicil=yonetici_sicil,
        ikinci_yonetici_sicil=ikinci_yonetici_sicil,
        ucuncu_yonetici_sicil=ucuncu_yonetici_sicil,
    )
    return PersonnelOrgHierarchyResult(
        phase="personnel_service_faz6",
        organization_unit_attached=bool(org_unit),
        manager_level_count=manager_count,
        manager_source="sicil",
    )


def attach_personnel_payload_org_hierarchy(
    user: Any,
    *,
    payload: PersonnelFormPayload,
    user_model: Any,
    db_session: Any,
    ensure_unit_exists: EnsureUnitExists,
    role_for_unit: str,
) -> PersonnelOrgHierarchyResult:
    """Bridge personnel add/edit payload organization and id-based manager fields."""
    org_unit = attach_organization_unit_to_user(
        user,
        birim=payload.birim,
        ust_birim=payload.ust_birim,
        role=role_for_unit,
        ensure_unit_exists=ensure_unit_exists,
    )
    manager_count = apply_manager_id_hierarchy(
        user,
        user_model=user_model,
        db_session=db_session,
        manager_1_id=payload.manager_1_id,
        manager_2_id=payload.manager_2_id,
        manager_3_id=payload.manager_3_id,
    )
    return PersonnelOrgHierarchyResult(
        phase="personnel_service_faz6",
        organization_unit_attached=bool(org_unit),
        manager_level_count=manager_count,
        manager_source="manager_id",
    )


def build_personnel_org_hierarchy_phase6_summary() -> dict[str, Any]:
    return {
        "phase": "personnel_service_faz6",
        "service": "org_hierarchy",
        "organization_unit_bridge": True,
        "manager_sicil_bridge": True,
        "manager_id_bridge": True,
        "db_commit": False,
        "db_rollback": False,
        "route_contract": "preserved",
    }
