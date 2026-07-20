from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import Mock

import sqlalchemy

from app.services import corporate_information_center
from app.services.cic import config_context, facade

MOVED_HELPERS = {"_clean_ids", "_has_settings_table", "_loads_json"}


def test_public_entries_use_canonical_settings_helpers() -> None:
    for name in MOVED_HELPERS:
        expected = getattr(config_context, name)
        assert getattr(facade, name) is expected, name
        assert getattr(corporate_information_center, name) is expected, name


def test_clean_ids_preserves_order_uniqueness_and_logs_bad_values(
    monkeypatch,
) -> None:
    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", Mock(return_value=logger))

    result = config_context._clean_ids(["2", 1, "2", "bad", None, 3])

    assert result == [2, 1, 3]
    assert logger.exception.call_count == 2


def test_loads_json_uses_canonical_success_empty_and_error_contracts(
    monkeypatch,
) -> None:
    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", Mock(return_value=logger))

    monkeypatch.setattr(
        config_context,
        "get_setting",
        lambda key, default: '{"ok": true}',
    )
    assert config_context._loads_json("sample", {}) == {"ok": True}

    monkeypatch.setattr(config_context, "get_setting", lambda key, default: "")
    fallback = {"fallback": True}
    assert config_context._loads_json("sample", fallback) is fallback

    monkeypatch.setattr(
        config_context,
        "get_setting",
        lambda key, default: "{bad",
    )
    assert config_context._loads_json("sample", fallback) is fallback
    logger.exception.assert_called_once()


def test_has_settings_table_preserves_true_and_false_contracts(
    monkeypatch,
) -> None:
    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", Mock(return_value=logger))

    inspector = SimpleNamespace(has_table=lambda name: name == "system_settings")
    monkeypatch.setattr(config_context, "db", SimpleNamespace(engine=object()))
    monkeypatch.setattr(sqlalchemy, "inspect", lambda engine: inspector)
    assert config_context._has_settings_table() is True

    def raise_inspect(engine):
        raise RuntimeError("inspection unavailable")

    monkeypatch.setattr(sqlalchemy, "inspect", raise_inspect)
    assert config_context._has_settings_table() is False
    logger.exception.assert_called_once()
