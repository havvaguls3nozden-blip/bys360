from __future__ import annotations

import logging
from datetime import date, datetime

from app.services.cic import cic_context, facade

HELPER = "_cic_v45_parse_date"


def test_v45_date_helper_resolves_to_canonical_owner() -> None:
    assert facade._cic_v45_parse_date is cic_context._cic_v45_parse_date


def test_v45_date_passthrough_contract_is_preserved() -> None:
    day = date(2024, 2, 29)
    moment = datetime(2024, 2, 29, 15, 45)

    assert cic_context._cic_v45_parse_date(None) is None
    assert cic_context._cic_v45_parse_date(day) is day
    assert cic_context._cic_v45_parse_date(moment) == day


def test_v45_excel_serial_date_contract_is_preserved() -> None:
    parse = cic_context._cic_v45_parse_date
    assert parse(25569) == date(1970, 1, 1)
    assert parse(45292) == date(2024, 1, 1)
    assert parse(45351.0) == date(2024, 2, 29)
    assert parse(20000) is None


def test_v45_text_date_formats_are_preserved() -> None:
    expected = date(2024, 2, 29)
    parse = cic_context._cic_v45_parse_date

    assert parse("29.02.2024") == expected
    assert parse("2024-02-29") == expected
    assert parse("29/02/24") == expected


def test_v45_invalid_date_returns_none_and_uses_canonical_logging(caplog) -> None:
    caplog.set_level(logging.ERROR, logger=cic_context.__name__)

    assert cic_context._cic_v45_parse_date("29.02.2023") is None

    assert caplog.records
    assert all(record.name == cic_context.__name__ for record in caplog.records)
    assert any("BYS360 SAFE V5" in record.getMessage() for record in caplog.records)


def test_facade_date_export_is_preserved() -> None:
    assert HELPER in facade.__all__
