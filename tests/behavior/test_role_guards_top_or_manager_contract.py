"""BYS360 DEFECT AQ: app/services/role_guards.py

Behavioral contract for `is_top_or_manager` (and its two thin wrappers
`can_view_strategic_performance`/`can_manage_strategic_targets`), calling
the real function directly against `SimpleNamespace` fake users -- no
mocking of the authorization decision itself.

`is_top_or_manager` used to substring-match `TOP_OR_MANAGER_TOKENS`
(partial word fragments, including the bare 2-char token "ik") against a
single role/role_name string -- an ordinary title like "Teknik Personel"
(Technical Staff) contains "ik" as a substring ("tekn-ik") and was
incorrectly granted the strategic-performance KPI dashboard and
strategic-target management routes. Each token is now a full canonical role
code checked via EXACT membership in `TOP_OR_MANAGER_ROLES`.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.role_guards import (
    TOP_OR_MANAGER_ROLES,
    can_manage_strategic_targets,
    can_view_strategic_performance,
    is_top_or_manager,
)


def _user(role: str | None, *, authenticated: bool = True) -> SimpleNamespace:
    return SimpleNamespace(role=role, is_authenticated=authenticated, is_admin=False, is_superuser=False)


@pytest.mark.parametrize("role", sorted(TOP_OR_MANAGER_ROLES))
def test_allows_every_canonical_top_or_manager_role(role):
    assert is_top_or_manager(_user(role)) is True
    assert can_view_strategic_performance(_user(role)) is True
    assert can_manage_strategic_targets(_user(role)) is True


@pytest.mark.parametrize(
    "role",
    [
        "Teknik Personel",
        "İstatistik Uzmanı",
        "Pratik Destek Uzmanı",
        "Lojistik Sorumlusu",
    ],
)
def test_denies_bare_ik_substring_lookalikes(role):
    # BYS360 DEFECT AQ adversarial case: none of these are actually İK/HR
    # staff -- they merely contain the bare "ik" token as a substring.
    assert is_top_or_manager(_user(role)) is False


def test_denies_baskanligi_uzmani_lookalike():
    assert is_top_or_manager(_user("Başkanlığı Uzmanı")) is False


def test_denies_unknown_role():
    assert is_top_or_manager(_user("temizlik_gorevlisi")) is False


def test_denies_unauthenticated_user_even_with_privileged_role():
    assert is_top_or_manager(_user("admin", authenticated=False)) is False


def test_denies_missing_or_none_user():
    assert is_top_or_manager(None) is False
    assert is_top_or_manager(_user(None)) is False


def test_allows_via_real_boolean_admin_flag_even_with_unrelated_role_text():
    user = _user("personel")
    user.is_admin = True
    assert is_top_or_manager(user) is True


def test_falls_back_to_role_name_attribute_when_role_missing():
    user = SimpleNamespace(role=None, role_name="mali_musavir", is_authenticated=True, is_admin=False, is_superuser=False)
    assert is_top_or_manager(user) is True
