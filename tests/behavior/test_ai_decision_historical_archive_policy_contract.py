"""BYS360 DEFECT AQ: app/services/ai_decision/historical_archive_policy.py

Behavioral contract for `can_view_archive_summary` / `can_view_archive_detail`,
calling the real functions directly against `SimpleNamespace` fake users --
no mocking of the authorization decision itself.

`can_view_archive_summary` used to fall back to a bare substring match
(`SUMMARY_ALLOWED_ROLE_PARTS`, including the 2-character token "ik") when a
role text was not an exact member of `DETAIL_ALLOWED_ROLES`. An ordinary
title such as "İktisat Uzmanı" (Economics Specialist) contains "ik" as a
substring ("ikt-isat") and was incorrectly granted company-wide archive
summary access. The fallback has been removed; `can_view_archive_summary`
now reuses the same exact-match `DETAIL_ALLOWED_ROLES` set its sibling
`can_view_archive_detail` already used correctly.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.ai_decision.historical_archive_policy import (
    DETAIL_ALLOWED_ROLES,
    can_view_archive_detail,
    can_view_archive_summary,
)


def _user(role: str | None) -> SimpleNamespace:
    return SimpleNamespace(role=role, id=1)


@pytest.mark.parametrize("role", sorted(DETAIL_ALLOWED_ROLES))
def test_can_view_archive_summary_true_for_every_canonical_allowed_role(role):
    assert can_view_archive_summary(_user(role)) is True


@pytest.mark.parametrize(
    "role",
    [
        "İktisat Uzmanı",
        "Teknik Personel",
        "İstatistik Uzmanı",
        "Klinik Psikolog",
        "Lojistik Sorumlusu",
    ],
)
def test_can_view_archive_summary_denies_bare_ik_substring_lookalikes(role):
    # BYS360 DEFECT AQ adversarial case: these are ordinary specialist
    # titles that merely CONTAIN the bare 2-char "ik" (İK/HR) token as a
    # substring -- none of them are actually İK/HR staff.
    assert can_view_archive_summary(_user(role)) is False


def test_can_view_archive_summary_denies_baskanligi_uzmani_lookalike():
    assert can_view_archive_summary(_user("Başkanlığı Uzmanı")) is False


def test_can_view_archive_summary_denies_unknown_role():
    assert can_view_archive_summary(_user("temizlik_gorevlisi")) is False


def test_can_view_archive_summary_denies_empty_or_missing_role():
    assert can_view_archive_summary(_user(None)) is False
    assert can_view_archive_summary(_user("")) is False
    assert can_view_archive_summary(SimpleNamespace()) is False


def test_can_view_archive_summary_allows_real_admin_and_president():
    assert can_view_archive_summary(_user("admin")) is True
    assert can_view_archive_summary(_user("baskan")) is True


def test_can_view_archive_detail_still_allows_self_view_regardless_of_role():
    # Sibling function's own-record fallback is unrelated to this fix and
    # must remain unaffected.
    viewer = _user("personel")
    viewer.id = 42
    assert can_view_archive_detail(viewer, target_user_id=42) is True
    assert can_view_archive_detail(viewer, target_user_id=99) is False
