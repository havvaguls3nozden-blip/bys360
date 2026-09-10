"""BYS360 DEFECT AR: several live call sites compared Turkish text for
equality via ``func.lower(column) == value.lower()``. SQLite's built-in SQL
LOWER() only folds ASCII letters, so a duplicate department name or a legacy
employee name typed with a Turkish capital İ was silently NOT detected as a
match on SQLite -- and PostgreSQL's exact behavior for the same comparison
could not be verified without production access. The fix normalizes both
sides in Python via app.utils.turkish_text.turkish_casefold instead of
relying on either database's native LOWER().

Positive cases prove two independently-typed representations of the same
Turkish word now fold to the same value. A negative case proves genuinely
different words still do not match (the fix must not become a broad
fuzzy-match).
"""
from __future__ import annotations

from app.utils.turkish_text import turkish_casefold


def test_turkish_dotted_capital_i_folds_to_match_lowercase_form():
    assert turkish_casefold("İnsan Kaynakları") == turkish_casefold("insan kaynakları")


def test_turkish_dotless_capital_i_folds_to_match_lowercase_form():
    assert turkish_casefold("BİLGİ İŞLEM") == turkish_casefold("bilgi işlem")


def test_ascii_capital_i_folds_to_turkish_dotless_i_not_ascii_i():
    # Real institutional data entered with a plain ASCII "I" instead of the
    # correct Turkish dotless "ı" should still be recognized as the same word.
    assert turkish_casefold("ISPARTA") == turkish_casefold("ısparta")


def test_plain_python_lower_would_have_failed_this_case():
    # Documents exactly why plain str.lower() was not sufficient on its own:
    # Python's own 'İ'.lower() expands to two codepoints (i + combining dot
    # above), which does not equal a plain single "i".
    assert "İ".lower() != "i"
    assert turkish_casefold("İ") == "i"


def test_genuinely_different_words_do_not_match():
    assert turkish_casefold("İnsan Kaynakları") != turkish_casefold("Bilgi İşlem")


def test_empty_and_none_values_fold_to_empty_string():
    assert turkish_casefold("") == ""
    assert turkish_casefold(None) == ""
