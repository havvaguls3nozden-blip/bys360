"""BYS360 DEFECT AQ: app/menu_registry.py

Behavioral contract for `_normalize_role_value` / `_is_president_approvals_
authorized_user`, calling the real functions directly against
`SimpleNamespace` fake users -- no mocking.

`_normalize_role_value` used to call `.lower()` before `.translate()`.
Python's `'İ'.lower()` (Turkish capital dotted I, U+0130) produces the
TWO-codepoint sequence 'i' + COMBINING DOT ABOVE (U+0307), not plain ASCII
'i' -- so the translate table's 'İ' -> 'i' entry was dead code, and any
role/unvan value containing capital İ (e.g. "SİSTEM YÖNETİCİSİ") left a
stray combining-dot codepoint in the normalized text, causing it to fail
exact-match comparison against the canonical "sistem_yoneticisi" value and
silently deny a legitimate admin/president the "Başkan Onayları" menu
entry. 'İ' is now folded to 'i' before `.lower()` runs.

`_is_president_approvals_authorized_user` and `_matches_role` were already
confirmed SAFE_EXACT_MATCH for the substring-matching dimension (no
containment/`in` checks) -- this file only proves the Unicode ordering fix,
it does not change or need adversarial substring-lookalike coverage.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.menu_registry import _is_president_approvals_authorized_user, _normalize_role_value


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Sistem Yöneticisi", "sistem_yoneticisi"),
        ("SİSTEM YÖNETİCİSİ", "sistem_yoneticisi"),
        ("sİstem yöneticisi", "sistem_yoneticisi"),
        ("Başkan", "baskan"),
        ("BAŞKAN", "baskan"),
        ("İstanbul Başkanlığı", "istanbul_baskanligi"),
        ("admin", "admin"),
    ],
)
def test_normalize_role_value_folds_turkish_capital_i_correctly(raw, expected):
    normalized = _normalize_role_value(raw)
    assert normalized == expected
    assert not any(ord(ch) == 0x0307 for ch in normalized), "stray combining dot above survived normalization"


def _user(role: str, *, authenticated: bool = True) -> SimpleNamespace:
    return SimpleNamespace(is_authenticated=authenticated, is_admin=False, is_superuser=False, role=role, role_name=None, user_type=None, unvan=None, title=None)


def test_is_president_approvals_authorized_user_true_for_all_caps_turkish_admin_title():
    # BYS360 DEFECT AQ: before the fix, this exact realistic all-caps HR
    # data-entry value ("SİSTEM YÖNETİCİSİ") failed to normalize to
    # "sistem_yoneticisi" and was incorrectly DENIED the Başkan Onayları
    # menu entry despite being a real system administrator.
    assert _is_president_approvals_authorized_user(_user("SİSTEM YÖNETİCİSİ")) is True


def test_is_president_approvals_authorized_user_true_for_correctly_capitalized_baskan():
    assert _is_president_approvals_authorized_user(_user("Başkan")) is True


def test_is_president_approvals_authorized_user_denies_baskanligi_uzmani_lookalike():
    assert _is_president_approvals_authorized_user(_user("Başkanlığı Uzmanı")) is False


def test_is_president_approvals_authorized_user_denies_unauthenticated():
    assert _is_president_approvals_authorized_user(_user("admin", authenticated=False)) is False
