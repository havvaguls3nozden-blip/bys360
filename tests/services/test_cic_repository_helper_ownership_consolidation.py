from __future__ import annotations

import ast
import json
from datetime import date, datetime
from pathlib import Path

from app.services.cic import (
    celebration_dates,
    cic_context,
    config_context,
    facade,
    misc_context,
    repository,
)

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_PATH = ROOT / "app/services/cic/repository.py"

MOVED_DEFINITIONS = {
    "_cic_auto_bool",
    "_cic_is_weekend",
    "_cic_v40_bool",
    "_cic_v45_bool",
    "_cic_v45_header_key",
    "_cic_v45_norm",
    "_cic_v45_norm_name",
    "_cic_v45_text",
    "_dumps_json",
    "_now",
    "get_setting",
    "set_setting",
}

CANONICAL_OWNERS = {
    "_cic_auto_bool": misc_context,
    "_cic_is_weekend": cic_context,
    "_cic_v40_bool": celebration_dates,
    "_cic_v45_bool": cic_context,
    "_cic_v45_header_key": cic_context,
    "_cic_v45_norm": cic_context,
    "_cic_v45_norm_name": cic_context,
    "_cic_v45_text": cic_context,
    "_dumps_json": config_context,
    "_now": config_context,
    "get_setting": config_context,
}


def _repository_tree() -> ast.Module:
    return ast.parse(REPOSITORY_PATH.read_text(encoding="utf-8"))


def test_repository_no_longer_defines_low_risk_helper_duplicates() -> None:
    definitions = {
        node.name
        for node in _repository_tree().body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert definitions.isdisjoint(MOVED_DEFINITIONS)


def test_repository_compatibility_names_resolve_to_canonical_helpers() -> None:
    for name, owner in CANONICAL_OWNERS.items():
        expected = getattr(owner, name)
        assert getattr(repository, name) is expected, name
        assert getattr(facade, name) is expected, name


def test_set_setting_has_only_the_canonical_public_owner() -> None:
    assert not hasattr(repository, "set_setting")
    assert facade.set_setting is config_context.set_setting


def test_boolean_date_and_normalization_contracts_are_preserved() -> None:
    assert repository._cic_auto_bool("evet") is True
    assert repository._cic_auto_bool("", default=True) is True
    assert repository._cic_is_weekend(datetime(2026, 7, 18, 9, 0)) is True
    assert repository._cic_is_weekend(datetime(2026, 7, 20, 9, 0)) is False
    assert repository._cic_v40_bool("aktif") is True
    assert repository._cic_v40_bool("pasif") is False
    assert repository._cic_v45_norm("Çanakkale Şehitleri") == "canakkalesehitleri"
    assert repository._cic_v45_norm_name("  Gülsen   Özden ") == "gulsen ozden"
    assert repository._cic_v45_bool("Evet") is True
    assert repository._cic_v45_bool("Hayır") is False
    assert repository._cic_v45_header_key("Doğum Tarihi") == "birth_date"


def test_json_and_remaining_repository_helpers_keep_behavior() -> None:
    payload = {"şehir": "Çanakkale", "aktif": True}
    dumped = repository._dumps_json(payload)
    assert json.loads(dumped) == payload
    assert "Çanakkale" in dumped
    assert repository._cic_v40_today(date(2026, 7, 20)) == date(2026, 7, 20)
    assert repository._cic_v45_parse_date("31.12.2024") == date(2024, 12, 31)


def test_removed_helper_implementations_leave_no_private_support_imports() -> None:
    source = REPOSITORY_PATH.read_text(encoding="utf-8")
    assert "_cic_v45_re" not in source
    assert "_cic_v45_unicodedata" not in source
    assert "from app.models import SystemSetting" not in source
