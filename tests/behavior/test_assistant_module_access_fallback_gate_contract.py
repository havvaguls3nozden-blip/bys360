"""BYS360 DEFECT AQ: app/services/assistant_module_access.py

Behavioral contract for `assistant_module_enabled_for_current_user`'s
uncatalogued-role fallback -- the path reached only when no DB-backed policy
row exists for the current user/role AND the role is not an exact member of
`CLOSED_ROLES`/`OPEN_ROLES`.

This fallback used to grant access via `any(token in role for token in
(...))` -- an ordinary title like "Başkanlığı Uzmanı" (not the president)
normalizes to contain "baskan" as a substring and was incorrectly granted
access to the Sanal Asistan (Virtual Assistant) module, which
`register_assistant_module_master_access`'s own `before_request` hook uses
as a real route gate (redirects/403s away from `/assistant`, `/asistan`,
etc. paths). The fallback now denies unconditionally; only an exact
`OPEN_ROLES` member (or a DB-backed policy row) grants access.

`_db_session` is monkeypatched to return `None` so these tests exercise only
the pure CLOSED_ROLES/OPEN_ROLES/fallback decision, matching the function's
own already-supported "no DB available" branch -- no Flask app or database
needed.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import app.services.assistant_module_access as assistant_module_access
from app.services.assistant_module_access import (
    CLOSED_ROLES,
    OPEN_ROLES,
    assistant_module_enabled_for_current_user,
)


@pytest.fixture(autouse=True)
def _no_db_session(monkeypatch):
    monkeypatch.setattr(assistant_module_access, "_db_session", lambda: None)


def _set_user(monkeypatch, role):
    monkeypatch.setattr(
        assistant_module_access,
        "current_user",
        SimpleNamespace(is_authenticated=True, role=role, role_label=None, unvan=None),
    )


@pytest.mark.parametrize("role", sorted(OPEN_ROLES))
def test_allows_every_canonical_open_role(monkeypatch, role):
    _set_user(monkeypatch, role)
    assert assistant_module_enabled_for_current_user() is True


@pytest.mark.parametrize("role", sorted(r for r in CLOSED_ROLES if r))
def test_denies_every_canonical_closed_role(monkeypatch, role):
    _set_user(monkeypatch, role)
    assert assistant_module_enabled_for_current_user() is False


@pytest.mark.parametrize(
    "role",
    [
        "Başkanlığı Uzmanı",
        "Grup Koordinasyon Ofisi Asistanı",
        "Sistem Destek Uzmanı",
        "Muhasebe ve Admin İşleri Sorumlusu",
    ],
)
def test_denies_uncatalogued_lookalike_role_substrings(monkeypatch, role):
    # BYS360 DEFECT AQ adversarial case: none of these normalize to an
    # exact OPEN_ROLES member, even though each contains a privileged
    # token as a substring.
    _set_user(monkeypatch, role)
    assert assistant_module_enabled_for_current_user() is False


def test_denies_unauthenticated_user(monkeypatch):
    monkeypatch.setattr(
        assistant_module_access,
        "current_user",
        SimpleNamespace(is_authenticated=False, role="admin"),
    )
    assert assistant_module_enabled_for_current_user() is False


def test_denies_missing_role_fields(monkeypatch):
    monkeypatch.setattr(
        assistant_module_access,
        "current_user",
        SimpleNamespace(is_authenticated=True, role=None, role_label=None, unvan=None),
    )
    assert assistant_module_enabled_for_current_user() is False
