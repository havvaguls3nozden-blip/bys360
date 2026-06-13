from __future__ import annotations



from typing import Any, Iterable

from sqlalchemy import func

from app.extensions import db


def _clean_exclusions(values: Iterable[str] | None, *, lowercase: bool) -> list[str]:
    cleaned: list[str] = []
    for value in values or []:
        text = str(value or '').strip()
        if not text:
            continue
        cleaned.append(text.lower() if lowercase else text)
    return cleaned


def _coerce_first_column(row: Any) -> Any:
    try:
        return row[0]
    except (TypeError, KeyError, IndexError):
        return row


def distinct_non_empty_values(
    column: Any,
    *,
    exclude: Iterable[str] | None = None,
    lowercase: bool = False,
    limit: int | None = None,
) -> list[str]:
    """Return distinct non-empty values with the emptiness filter pushed to SQL.

    This helper is intentionally small and read-only. It replaces repeated
    ``query.distinct().all(); if row[0]`` dropdown patterns so large option
    lists are filtered before rows are materialized.
    """
    trimmed_column = func.trim(column)
    select_column = func.lower(trimmed_column) if lowercase else column
    compare_column = func.lower(trimmed_column) if lowercase else trimmed_column

    query = db.session.query(select_column).filter(
        column.isnot(None),
        trimmed_column != '',
    )

    exclusions = _clean_exclusions(exclude, lowercase=lowercase)
    if exclusions:
        query = query.filter(~compare_column.in_(exclusions))

    query = query.distinct().order_by(select_column.asc())
    if limit is not None:
        try:
            safe_limit = max(int(limit), 1)
        except (TypeError, ValueError):
            safe_limit = 1
        query = query.limit(safe_limit)

    values: list[str] = []
    seen: set[str] = set()
    for row in query:
        raw_value = _coerce_first_column(row)
        value = str(raw_value or '').strip()
        if lowercase:
            value = value.lower()
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values


def distinct_normalized_non_empty_values(column: Any, *, limit: int | None = None) -> list[str]:
    """Lowercase + trim distinct option helper for module/status keys."""
    return distinct_non_empty_values(column, lowercase=True, limit=limit)
