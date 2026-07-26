from __future__ import annotations

import ast
import logging
from datetime import date, datetime
from pathlib import Path
from typing import cast
from unittest.mock import Mock

from app.services import corporate_information_center
from app.services.cic import celebration_dates, cic_context, facade

ROOT = Path(__file__).resolve().parents[2]
CIC_CONTEXT_PATH = ROOT / "app/services/cic/cic_context.py"
QUERY_SERVICE_PATH = ROOT / "app/services/cic/query_service.py"

DATE_HELPERS = {
    "_cic_v40_days_until",
    "_cic_v40_mmdd",
    "_cic_v40_parse_date",
    "_cic_v40_today",
}


def _top_level_definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_date_and_weekday_helpers_have_canonical_owners() -> None:
    for name in DATE_HELPERS:
        expected = getattr(celebration_dates, name)
        assert getattr(facade, name) is expected, name
        assert getattr(corporate_information_center, name) is expected, name

    expected_weekday = cic_context._cic_weekday_name_tr
    assert facade._cic_weekday_name_tr is expected_weekday
    assert corporate_information_center._cic_weekday_name_tr is expected_weekday


def test_cic_context_reexports_canonical_days_until_without_second_body() -> None:
    assert "_cic_v40_days_until" not in _top_level_definitions(CIC_CONTEXT_PATH)
    assert cic_context._cic_v40_days_until is celebration_dates._cic_v40_days_until


def test_parse_date_preserves_supported_value_contracts() -> None:
    expected = date(2026, 7, 20)
    values = (
        expected,
        datetime(2026, 7, 20, 14, 30),
        "2026-07-20",
        "20.07.2026",
        "20/07/2026",
        "2026/07/20",
    )

    for value in values:
        assert celebration_dates._cic_v40_parse_date(value) == expected

    assert celebration_dates._cic_v40_parse_date(None) is None
    assert celebration_dates._cic_v40_parse_date("  ") is None


def test_parse_date_invalid_value_uses_canonical_logging_contract(
    monkeypatch,
) -> None:
    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", Mock(return_value=logger))

    assert celebration_dates._cic_v40_parse_date("not-a-date") is None
    assert logger.exception.call_count == 4


def test_today_preserves_passthrough_and_fallback_contracts(
    monkeypatch,
) -> None:
    expected = date(2026, 7, 20)
    assert celebration_dates._cic_v40_today(expected) == expected
    assert celebration_dates._cic_v40_today(
        datetime(2026, 7, 20, 9, 15)
    ) == expected

    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", Mock(return_value=logger))

    def raise_now() -> datetime:
        raise RuntimeError("clock unavailable")

    monkeypatch.setattr(celebration_dates, "_now", raise_now)
    assert celebration_dates._cic_v40_today() == date.today()
    logger.exception.assert_called_once()


def test_mmdd_and_days_until_preserve_current_calendar_contracts(
    monkeypatch,
) -> None:
    today = date(2026, 7, 20)

    assert celebration_dates._cic_v40_mmdd(today) == "07-20"
    assert celebration_dates._cic_v40_mmdd(None) == ""
    assert celebration_dates._cic_v40_days_until("07-20", today) == 0
    assert celebration_dates._cic_v40_days_until("07-25", today) == 5
    assert celebration_dates._cic_v40_days_until("07-19", today) == 364
    assert celebration_dates._cic_v40_days_until(
        "02-29",
        date(2024, 2, 28),
    ) == 1

    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", Mock(return_value=logger))
    assert celebration_dates._cic_v40_days_until(
        "02-29",
        date(2025, 1, 1),
    ) is None
    assert celebration_dates._cic_v40_days_until("bad", today) is None
    assert logger.exception.call_count == 2


def test_weekday_name_preserves_turkish_names_and_invalid_fallback(
    monkeypatch,
) -> None:
    names = (
        "Pazartesi",
        "Salı",
        "Çarşamba",
        "Perşembe",
        "Cuma",
        "Cumartesi",
        "Pazar",
    )
    monday = datetime(2026, 7, 20)

    for offset, expected in enumerate(names):
        current = datetime.fromordinal(monday.toordinal() + offset)
        assert cic_context._cic_weekday_name_tr(current) == expected

    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", Mock(return_value=logger))
    # _cic_weekday_name_tr's try/except tolerates any input lacking
    # .weekday() (verified in app/services/cic/cic_context.py), returning
    # "Bilinmiyor" -- this deliberately exercises that fallback path.
    assert cic_context._cic_weekday_name_tr(cast(datetime, object())) == "Bilinmiyor"
    logger.exception.assert_called_once()


def test_query_service_uses_canonical_date_owner() -> None:
    query_source = QUERY_SERVICE_PATH.read_text(encoding="utf-8")
    assert (
        "from app.services.cic.cic_context import _cic_v40_days_until"
        not in query_source
    )
    assert "from app.services.cic.celebration_dates import (" in query_source
