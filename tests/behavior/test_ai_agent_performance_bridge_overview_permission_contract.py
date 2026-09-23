"""BYS360 DEFECT AQ: app/services/ai_agent/performance_bridge.py

Behavioral contract for `has_performance_overview_permission`, calling the
real function directly against `SimpleNamespace` fake users -- no mocking of
the authorization decision itself.

The function used to concatenate 8 role-bearing fields into one text blob
and substring-match `PRIVILEGED_ROLE_KEYWORDS` (including the bare 2-char
token "ik") against it -- an ordinary title like "Lojistik Sorumlusu"
(Logistics Officer) contains "ik" as a substring ("loj-ist-ik") and was
incorrectly granted company-wide performance-overview aggregate counts. Each
role-bearing field is now normalized and checked individually for EXACT
membership in `PRIVILEGED_ROLE_VALUES`.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.ai_agent.performance_bridge import (
    PRIVILEGED_ROLE_VALUES,
    has_performance_overview_permission,
)


def _user(**kwargs) -> SimpleNamespace:
    base = {
        "role": None, "role_name": None, "user_role": None, "role_key": None,
        "title": None, "unvan": None, "position": None, "roles": None,
        "is_admin": False, "is_superuser": False, "is_system_admin": False,
        "is_president": False, "is_manager": False,
    }
    base.update(kwargs)
    return SimpleNamespace(**base)


@pytest.mark.parametrize("role", sorted(PRIVILEGED_ROLE_VALUES))
def test_allows_every_canonical_privileged_role_value(role):
    assert has_performance_overview_permission(_user(role=role)) is True


@pytest.mark.parametrize(
    "role",
    [
        "Lojistik Sorumlusu",
        "Teknik Personel",
        "Pratik Destek Uzmanı",
        "İstatistik Uzmanı",
        "Sistem Destek Uzmanı",
    ],
)
def test_denies_bare_ik_or_sistem_substring_lookalikes(role):
    # BYS360 DEFECT AQ adversarial case: none of these are actually
    # İK/HR staff or system administrators -- they merely contain a
    # privileged token as a substring within an unrelated title.
    assert has_performance_overview_permission(_user(role=role)) is False


def test_denies_baskanligi_uzmani_lookalike():
    assert has_performance_overview_permission(_user(unvan="Başkanlığı Uzmanı")) is False


def test_denies_unknown_role():
    assert has_performance_overview_permission(_user(role="temizlik_gorevlisi")) is False


def test_denies_when_no_role_fields_and_no_privileged_flags_set():
    assert has_performance_overview_permission(_user()) is False


def test_allows_via_real_boolean_admin_flag_even_with_unrelated_role_text():
    assert has_performance_overview_permission(_user(role="personel", is_admin=True)) is True


def test_allows_via_roles_collection_exact_name_match():
    role_obj = SimpleNamespace(name="baskan")
    assert has_performance_overview_permission(_user(roles=[role_obj])) is True


def test_denies_roles_collection_with_lookalike_name():
    role_obj = SimpleNamespace(name="Başkanlığı Uzmanı")
    assert has_performance_overview_permission(_user(roles=[role_obj])) is False
