"""BYS360 DEFECT AQ: app/services/portal_permission_matrix.py

Behavioral contract for `_norm`, the role normalizer feeding
`portal_permission_allowed`'s role-based portal feature-permission lookups
(`PORTAL_DEFAULTS`, `RoleMenuDefault` exact-key queries).

`_norm` used to call `.lower()` before `.translate()`. Python's
`'İ'.lower()` (Turkish capital dotted I, U+0130) produces the two-codepoint
sequence 'i' + COMBINING DOT ABOVE (U+0307), not plain ASCII 'i' -- so the
translate table's uppercase-side entries (built for pre-lower text) were
entirely dead code, and any role value containing capital İ (e.g. a
realistic all-caps HR value "İK") left a stray combining-dot codepoint in
the normalized text, causing it to fail exact-match lookup against the
canonical "ik" role key and silently deny that role its portal permissions.
"""
from __future__ import annotations

import pytest

from app.services.portal_permission_matrix import PORTAL_DEFAULTS, _norm


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("İK", "ik"),
        ("SİSTEM YÖNETİCİSİ", "sistem_yoneticisi"),
        ("Koordinatör", "koordinator"),
        ("Grup Başkanı", "grup_baskani"),
        ("Mali Müşavir", "mali_musavir"),
    ],
)
def test_norm_folds_turkish_capital_i_correctly(raw, expected):
    normalized = _norm(raw)
    assert normalized == expected
    assert not any(ord(ch) == 0x0307 for ch in normalized), "stray combining dot above survived normalization"


def test_norm_result_matches_a_real_portal_defaults_role_key():
    # "İK" is real HR data-entry capitalization for the "ik" role key.
    assert _norm("İK") in PORTAL_DEFAULTS
