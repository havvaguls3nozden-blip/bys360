"""Dialect-independent Turkish-aware case folding for equality comparisons.

BYS360 DEFECT AR: several call sites compared Turkish text for equality via
``func.lower(column) == value.lower()``. SQLite's built-in SQL ``LOWER()``
only folds ASCII letters, leaving Turkish letters (İ, I, Ş, Ğ, Ö, Ü, Ç)
unchanged, while PostgreSQL's behavior for the same input could not be
verified without connecting to production. Rather than depend on either
database's native ``LOWER()`` for Turkish text, this normalizes both sides
of a comparison in Python instead.

Plain ``str.lower()`` alone is not enough either: Python's own
``'İ'.lower()`` (Turkish capital dotted I, U+0130) produces the *two*
codepoints ``'i' + COMBINING DOT ABOVE (U+0307)``, not plain ASCII ``'i'``,
so two representations of the same word ("İnsan" vs. "insan") would still
compare unequal under plain ``.lower()``. Replacing the two Turkish-specific
letters before folding avoids that trap.
"""
from __future__ import annotations


def turkish_casefold(value: str | None) -> str:
    """Return a case-insensitive, Turkish-safe fold of ``value`` for equality
    comparisons. Not a canonical/display form -- only guaranteed to be
    symmetric for two independently-typed representations of the same text.
    """
    if not value:
        return ""
    return value.strip().replace("İ", "i").replace("I", "ı").lower()
