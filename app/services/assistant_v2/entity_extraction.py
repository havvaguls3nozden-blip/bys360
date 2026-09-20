"""BYS360 Assistant V2 -- deterministic, bounded entity extraction.

Pure, stdlib-only, regex/rule-based recognizers for a small, closed set of
BYS360 concepts (year, period reference, sicil_no, status keyword, and a
low-confidence "possible person name" span). No entity here is ever sent to
an external classifier -- everything is decided by this module's own
explicit rules. Ambiguous or unconfirmed entities are returned with
`confident=False` and the caller (the intent/response layer) must ask for
clarification rather than silently assume the extraction is correct --
this module never guesses a *specific* employee's identity from a name
fragment; it only flags that a name-shaped span exists.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_YEAR_RE = re.compile(r"\b(20[2-3]\d)\b")
_PERIOD_SLASH_RE = re.compile(r"\b(20[2-3]\d)\s*/\s*([1-4])\b")
_PERIOD_ORDINAL_RE = re.compile(
    r"\b(birinci|ikinci|üçüncü|dördüncü|1\.|2\.|3\.|4\.)\s*d[öo]nem", re.IGNORECASE
)
_SICIL_RE = re.compile(r"\bsicil(?:\s*no)?\s*[:\-]?\s*(\d{3,10})\b", re.IGNORECASE)
_BARE_NUMBER_ID_RE = re.compile(r"\b(\d{4,10})\b")

_ORDINAL_TO_INDEX = {
    "birinci": 1, "1.": 1,
    "ikinci": 2, "2.": 2,
    "üçüncü": 3, "3.": 3,
    "dördüncü": 4, "4.": 4,
}

_STATUS_KEYWORDS = {
    "tamamlanmamış": "incomplete",
    "tamamlanmayan": "incomplete",
    "eksik": "incomplete",
    "bekleyen": "pending",
    "bekliyor": "pending",
    "tamamlandı": "completed",
    "tamamlanan": "completed",
    "açık": "open",
    "kapalı": "closed",
    "kapanmış": "closed",
    "aktif": "active",
    "pasif": "inactive",
}

# Very small, conservative name-shaped-span detector: two consecutive
# Title-Case Turkish words (allows Turkish uppercase letters) with no digits
# -- deliberately NOT an attempt to resolve this to a real User row. The
# caller must look the span up against real personnel data and treat a
# non-match or multiple-match as ambiguous.
_NAME_SPAN_RE = re.compile(
    r"\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+)\s+([A-ZÇĞİÖŞÜ][a-zçğıöşü]+)\b"
)


@dataclass(frozen=True)
class ExtractedPeriodReference:
    year: int | None
    period_index: int | None
    raw_text: str
    confident: bool


@dataclass(frozen=True)
class ExtractedEntities:
    years: tuple[int, ...]
    period_references: tuple[ExtractedPeriodReference, ...]
    sicil_no: str | None
    status_keywords: tuple[str, ...]
    possible_person_name_spans: tuple[str, ...]


def _extract_period_references(text: str) -> tuple[ExtractedPeriodReference, ...]:
    results: list[ExtractedPeriodReference] = []
    for match in _PERIOD_SLASH_RE.finditer(text):
        results.append(
            ExtractedPeriodReference(
                year=int(match.group(1)),
                period_index=int(match.group(2)),
                raw_text=match.group(0),
                confident=True,
            )
        )
    for match in _PERIOD_ORDINAL_RE.finditer(text):
        ordinal_token = match.group(1).lower()
        index = _ORDINAL_TO_INDEX.get(ordinal_token)
        results.append(
            ExtractedPeriodReference(
                year=None,
                period_index=index,
                raw_text=match.group(0),
                # No explicit year given ("ikinci dönem" alone) -- caller
                # must resolve which year via conversation context or the
                # active-period capability; this extraction is intentionally
                # marked NOT confident on its own.
                confident=False,
            )
        )
    return tuple(results)


def extract_entities(text: str) -> ExtractedEntities:
    """Runs every recognizer over `text` and returns whatever it finds.
    Finding nothing for a category is normal and expected -- callers must
    treat an empty result as "not specified", never infer a default."""
    raw = text or ""

    period_references = _extract_period_references(raw)
    years_from_periods = {p.year for p in period_references if p.year is not None}
    years = tuple(sorted({int(m.group(1)) for m in _YEAR_RE.finditer(raw)} | years_from_periods))

    sicil_match = _SICIL_RE.search(raw)
    sicil_no = sicil_match.group(1) if sicil_match else None
    if sicil_no is None:
        # A bare long number with no "sicil" label nearby is a WEAKER
        # signal -- only used if nothing else claimed it, and the caller is
        # expected to confirm it against a real record, not assume a match.
        bare_match = _BARE_NUMBER_ID_RE.search(raw)
        if bare_match and bare_match.group(1) not in {str(y) for y in years}:
            sicil_no = bare_match.group(1)

    status_keywords = tuple(
        sorted({label for token, label in _STATUS_KEYWORDS.items() if token in raw.lower()})
    )

    name_spans = tuple(f"{m.group(1)} {m.group(2)}" for m in _NAME_SPAN_RE.finditer(raw))

    return ExtractedEntities(
        years=years,
        period_references=period_references,
        sicil_no=sicil_no,
        status_keywords=status_keywords,
        possible_person_name_spans=name_spans,
    )


__all__ = ["ExtractedPeriodReference", "ExtractedEntities", "extract_entities"]
