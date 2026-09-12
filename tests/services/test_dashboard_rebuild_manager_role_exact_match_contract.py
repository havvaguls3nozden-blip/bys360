"""BYS360 DEFECT FS (Final Sweep A2-04): app/services/dashboard_rebuild_
service.py::_is_manager() previously used a substring fallback
(`"baskan" in role or "başkan" in role or "admin" in role`) on top of its
exact-match MANAGER_ROLES check. Any role string merely *containing* those
letters (e.g. a hypothetical "personel_baskanligi_uzmani"-style role) would
be misclassified as a manager, surfacing manager-only quick-action
navigation links ("Başkan Onayları", "Personel Yönetimi", "AI Karar Destek
Merkezi") to a non-manager. UI/navigation exposure only -- the flag never
gated real dashboard data (see _resolve_scope_ids, an independent
exact-match function used for all actual scope filtering, confirmed
unchanged by this fix and re-asserted below).

Fix: exact membership in MANAGER_ROLES only, no substring fallback.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.services.dashboard_rebuild_service import (
    GLOBAL_ROLES,
    MANAGER_ROLES,
    _is_manager,
    _resolve_scope_ids,
)


def _user(role: str) -> SimpleNamespace:
    return SimpleNamespace(role=role, id=1)


def test_substring_collision_role_is_not_classified_as_manager():
    # Before the fix: "baskan" in "personel_baskanligi_uzmani" -> True (bug).
    assert _is_manager(_user("personel_baskanligi_uzmani")) is False


def test_substring_collision_admin_role_is_not_classified_as_manager():
    assert _is_manager(_user("sub_admin_helper")) is False


def test_real_manager_roles_still_classified_as_manager():
    for role in MANAGER_ROLES:
        assert _is_manager(_user(role)) is True, role


def test_real_global_roles_still_classified_as_manager():
    for role in GLOBAL_ROLES:
        assert _is_manager(_user(role)) is True, role


def test_plain_personnel_role_is_not_a_manager():
    assert _is_manager(_user("personel")) is False


def test_backend_scope_resolution_unaffected_by_this_fix():
    # _resolve_scope_ids is a separate, exact-match-only function (checks
    # GLOBAL_ROLES, not MANAGER_ROLES/_is_manager) -- confirms this fix
    # (to _is_manager, UI-only) leaves actual data scoping untouched.
    # A real "admin" (GLOBAL_ROLES) still resolves to unrestricted (None).
    assert _resolve_scope_ids(_user("admin")) is None
    # The substring-collision role is not in GLOBAL_ROLES either way, so its
    # scope was already (correctly) restricted before and after this fix.
    assert "personel_baskanligi_uzmani" not in GLOBAL_ROLES
