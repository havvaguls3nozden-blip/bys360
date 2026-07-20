from __future__ import annotations

import ast
import logging
from datetime import date, datetime
from pathlib import Path

from app.services.cic import cic_context, facade, repository

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_PATH = ROOT / "app/services/cic/repository.py"
HELPER = "_cic_v45_parse_date"


def _repository_definitions() -> set[str]:
    tree = ast.parse(REPOSITORY_PATH.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_repository_no_longer_defines_v45_date_helper() -> None:
    assert HELPER not in _repository_definitions()


def test_v45_date_helper_resolves_to_canonical_owner() -> None:
    assert repository._cic_v45_parse_date is cic_context._cic_v45_parse_date
    assert facade._cic_v45_parse_date is cic_context._cic_v45_parse_date


def test_v45_date_passthrough_contract_is_preserved() -> None:
    day = date(2024, 2, 29)
    moment = datetime(2024, 2, 29, 15, 45)

    assert repository._cic_v45_parse_date(None) is None
    assert repository._cic_v45_parse_date(day) is day
    assert repository._cic_v45_parse_date(moment) == day


def test_v45_excel_serial_date_contract_is_preserved() -> None:
    assert repository._cic_v45_parse_date(25569) == date(1970, 1, 1)
    assert repository._cic_v45_parse_date(45292) == date(2024, 1, 1)
    assert repository._cic_v45_parse_date(45351.0) == date(2024, 2, 29)
    assert repository._cic_v45_parse_date(20000) is None


def test_v45_text_date_formats_are_preserved() -> None:
    expected = date(2024, 2, 29)

    assert repository._cic_v45_parse_date("29.02.2024") == expected
    assert repository._cic_v45_parse_date("2024-02-29") == expected
    assert repository._cic_v45_parse_date("29/02/24") == expected


def test_v45_invalid_date_returns_none_and_uses_canonical_logging(caplog) -> None:
    caplog.set_level(logging.ERROR, logger=cic_context.__name__)

    assert repository._cic_v45_parse_date("29.02.2023") is None

    assert caplog.records
    assert all(record.name == cic_context.__name__ for record in caplog.records)
    assert any("BYS360 SAFE V5" in record.getMessage() for record in caplog.records)


def test_repository_date_compatibility_export_is_preserved() -> None:
    assert HELPER in repository.__all__
