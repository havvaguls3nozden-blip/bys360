from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import Mock

import sqlalchemy

from app.services import corporate_information_center
from app.services.cic import config_context, facade

MOVED_HELPERS = {"_clean_ids", "_has_settings_table", "_loads_json"}


def _scoped_get_logger(target_module, fake_logger):
    """``logging.getLogger`` replacement that hands back ``fake_logger``
    only for ``target_module``'s own name, delegating every other call --
    including pytest's own internal logging-plugin calls made while this
    monkeypatch is active -- to the real ``logging.getLogger``. Replacing
    the whole factory unconditionally (``Mock(return_value=...)``) let a
    prior version of this test hand the fake logger to unrelated callers
    too, which could corrupt pytest's own global logging manager state for
    the remainder of the session (BYS360 Phase 10G)."""
    real_get_logger = logging.getLogger

    def _get_logger(name=None):
        if name == target_module.__name__:
            return fake_logger
        return real_get_logger(name)

    return _get_logger


def test_public_entries_use_canonical_settings_helpers() -> None:
    for name in MOVED_HELPERS:
        expected = getattr(config_context, name)
        assert getattr(facade, name) is expected, name
        assert getattr(corporate_information_center, name) is expected, name


def test_clean_ids_preserves_order_uniqueness_and_logs_bad_values(
    monkeypatch,
) -> None:
    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", _scoped_get_logger(config_context, logger))

    result = config_context._clean_ids(["2", 1, "2", "bad", None, 3])

    assert result == [2, 1, 3]
    assert logger.exception.call_count == 2


def test_loads_json_uses_canonical_success_empty_and_error_contracts(
    monkeypatch,
) -> None:
    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", _scoped_get_logger(config_context, logger))

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
    monkeypatch.setattr(logging, "getLogger", _scoped_get_logger(config_context, logger))

    inspector = SimpleNamespace(has_table=lambda name: name == "system_settings")
    monkeypatch.setattr(config_context, "db", SimpleNamespace(engine=object()))
    monkeypatch.setattr(sqlalchemy, "inspect", lambda engine: inspector)
    assert config_context._has_settings_table() is True

    def raise_inspect(engine):
        raise RuntimeError("inspection unavailable")

    monkeypatch.setattr(sqlalchemy, "inspect", raise_inspect)
    assert config_context._has_settings_table() is False
    logger.exception.assert_called_once()


def test_logging_getlogger_patches_above_do_not_leak_into_global_manager_state() -> None:
    """Regression guard (BYS360 Phase 10G): the tests above monkeypatch
    ``logging.getLogger`` while exercising a fake logger. Earlier this
    module replaced the whole factory unconditionally, which could hand
    the fake logger to unrelated callers (including pytest's own logging
    plugin) during those tests' execution window and corrupt
    ``logging.root.manager.loggerDict`` for the rest of the pytest
    session -- surfacing far downstream as pytest's own sessionfinish
    hook crashing with "TypeError: 'Mock' object is not iterable". This
    must hold regardless of test execution order, so it does not assume
    it runs immediately after any specific test above."""
    manager = logging.getLogger().manager
    assert hasattr(manager.loggerDict, "values")
    # The real regression signature was exactly this call raising
    # TypeError because loggerDict had become a non-iterable Mock.
    list(manager.loggerDict.values())

    probe = logging.getLogger("bys360.phase10g.regression_probe")
    probe.info("regression probe log line")
