from __future__ import annotations

import ast
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import sqlalchemy

from app.services import corporate_information_center
from app.services.cic import config_context, facade, repository

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_PATH = ROOT / "app/services/cic/repository.py"
MOVED_HELPERS = {"_clean_ids", "_has_settings_table", "_loads_json"}


def _repository_tree() -> ast.Module:
    return ast.parse(REPOSITORY_PATH.read_text(encoding="utf-8"))


def test_repository_no_longer_defines_settings_storage_helpers() -> None:
    definitions = {
        node.name
        for node in _repository_tree().body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert definitions.isdisjoint(MOVED_HELPERS)


def test_repository_and_public_entries_use_canonical_settings_helpers() -> None:
    for name in MOVED_HELPERS:
        expected = getattr(config_context, name)
        assert getattr(repository, name) is expected, name
        assert getattr(facade, name) is expected, name
        assert getattr(corporate_information_center, name) is expected, name


def test_clean_ids_preserves_order_uniqueness_and_logs_bad_values(
    monkeypatch,
) -> None:
    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", Mock(return_value=logger))

    result = repository._clean_ids(["2", 1, "2", "bad", None, 3])

    assert result == [2, 1, 3]
    assert logger.exception.call_count == 2


def test_loads_json_uses_canonical_success_empty_and_error_contracts(
    monkeypatch,
) -> None:
    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", Mock(return_value=logger))

    monkeypatch.setattr(config_context, "get_setting", lambda key, default: '{"ok": true}')
    assert repository._loads_json("sample", {}) == {"ok": True}

    monkeypatch.setattr(config_context, "get_setting", lambda key, default: "")
    fallback = {"fallback": True}
    assert repository._loads_json("sample", fallback) is fallback

    monkeypatch.setattr(config_context, "get_setting", lambda key, default: "{bad")
    assert repository._loads_json("sample", fallback) is fallback
    logger.exception.assert_called_once()


def test_has_settings_table_preserves_true_and_false_contracts(
    monkeypatch,
) -> None:
    logger = Mock()
    monkeypatch.setattr(logging, "getLogger", Mock(return_value=logger))

    inspector = SimpleNamespace(has_table=lambda name: name == "system_settings")
    monkeypatch.setattr(config_context, "db", SimpleNamespace(engine=object()))
    monkeypatch.setattr(sqlalchemy, "inspect", lambda engine: inspector)
    assert repository._has_settings_table() is True

    def raise_inspect(engine):
        raise RuntimeError("inspection unavailable")

    monkeypatch.setattr(sqlalchemy, "inspect", raise_inspect)
    assert repository._has_settings_table() is False
    logger.exception.assert_called_once()


def test_repository_drops_support_imports_owned_by_config_context() -> None:
    source = REPOSITORY_PATH.read_text(encoding="utf-8")
    tree = _repository_tree()

    imported_names = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert "sa_inspect" not in imported_names
    assert "db" not in imported_names
    assert "json" not in imported_names
    assert "Any" not in imported_names
    assert "BYS360 P7 migrated CIC settings repository helpers" not in source
