"""BYS360 Assistant V2 -- native Turkish language helpers.

Small, pure, well-tested formatting functions used by `response_composer.py`
to turn structured capability data into natural Turkish sentences. Every
function here is deterministic and stdlib-only -- no external NLP library,
no model call. This module knows nothing about capabilities, permissions,
or data sources; it only knows how to phrase Turkish text given already-
decided facts (count, dates, list items), keeping business logic and
language formatting separate (an explicit project requirement).

Turkish grammar note: unlike English, Turkish nouns stay in their singular
form after a numeral ("4 personel", not "4 personeller") -- `count_phrase`
relies on this and does not attempt noun pluralization.
"""
from __future__ import annotations

from datetime import date, datetime

_TURKISH_MONTHS = (
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
)

_VOWELS_BACK = set("aıou")
_VOWELS_FRONT = set("eiöü")


def _last_vowel(word: str) -> str | None:
    for ch in reversed(word.lower()):
        if ch in _VOWELS_BACK or ch in _VOWELS_FRONT:
            return ch
    return None


def locative_suffix(word: str) -> str:
    """Returns the correct Turkish locative-case suffix ("'de"/"'da") for a
    word, by simple two-way (front/back) vowel harmony on its last vowel.
    This is a deliberately small, safe subset of real Turkish vowel harmony
    (it does not handle consonant softening or the e/i-form distinction) --
    good enough for appending to proper nouns like unit/module names in
    generated sentences, not meant as a general-purpose morphology engine."""
    last = _last_vowel(word)
    if last in _VOWELS_FRONT:
        return "'de"
    return "'da"


def count_phrase(count: int, noun: str) -> str:
    """'4 personel', '1 anket', '0 kayıt' -- Turkish nouns do not pluralize
    after a numeral."""
    return f"{count} {noun}"


def format_date_tr(value: date | datetime | str | None) -> str | None:
    """ISO-ish date/datetime -> '1 Ocak 2026'. Returns None for anything it
    cannot parse (callers must handle that -- this function never guesses a
    date)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        d = value.date()
    elif isinstance(value, date):
        d = value
    elif isinstance(value, str):
        try:
            d = date.fromisoformat(value[:10])
        except ValueError:
            return None
    else:
        return None
    return f"{d.day} {_TURKISH_MONTHS[d.month - 1]} {d.year}"


def format_list_tr(items: list[str], *, max_items: int = 10) -> str:
    """['A', 'B', 'C'] -> 'A, B ve C'. Truncates with a Turkish '... ve N
    diğer' suffix when there are more than max_items entries -- never
    silently drops the count of how many were omitted."""
    cleaned = [str(item) for item in items if str(item).strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    shown = cleaned[:max_items]
    remainder = len(cleaned) - len(shown)
    if remainder > 0:
        return ", ".join(shown) + f" ve {remainder} diğer"
    if len(shown) == 2:
        return f"{shown[0]} ve {shown[1]}"
    return ", ".join(shown[:-1]) + f" ve {shown[-1]}"


def yes_no_phrase(value: bool, *, yes: str = "Evet", no: str = "Hayır") -> str:
    return yes if value else no


def access_denied_phrase(reason: str | None = None) -> str:
    base = "Bu bilgiyi görüntüleyemiyorum çünkü hesabınız için gerekli erişim yetkisi etkin değil."
    return f"{base} {reason}".strip() if reason else base


def no_data_phrase(subject: str | None = None) -> str:
    if subject:
        return f"{subject} için eşleşen bir kayıt bulunamadı."
    return "Bu istekle eşleşen bir kayıt bulunamadı."


def source_attribution_phrase(source_labels: list[str]) -> str:
    cleaned = [label for label in source_labels if label]
    if not cleaned:
        return ""
    return f"Kaynak: {format_list_tr(cleaned)}"


def comparison_phrase(*, label_a: str, value_a: int | float, label_b: str, value_b: int | float) -> str:
    if value_a == value_b:
        return f"{label_a} ile {label_b} eşit ({value_a})."
    higher, lower = (label_a, label_b) if value_a > value_b else (label_b, label_a)
    higher_value = max(value_a, value_b)
    lower_value = min(value_a, value_b)
    return f"{higher} ({higher_value}), {lower}'e ({lower_value}) göre daha yüksek."


__all__ = [
    "locative_suffix",
    "count_phrase",
    "format_date_tr",
    "format_list_tr",
    "yes_no_phrase",
    "access_denied_phrase",
    "no_data_phrase",
    "source_attribution_phrase",
    "comparison_phrase",
]
