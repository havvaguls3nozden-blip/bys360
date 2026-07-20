from __future__ import annotations

import json
from datetime import date, datetime

from app.services.cic import (
    celebration_dates,
    cic_context,
    config_context,
    facade,
    misc_context,
)

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


def test_facade_compatibility_names_resolve_to_canonical_helpers() -> None:
    for name, owner in CANONICAL_OWNERS.items():
        assert getattr(facade, name) is getattr(owner, name), name


def test_set_setting_has_only_the_canonical_public_owner() -> None:
    assert facade.set_setting is config_context.set_setting


def test_boolean_date_and_normalization_contracts_are_preserved() -> None:
    assert facade._cic_auto_bool("evet") is True
    assert facade._cic_auto_bool("", default=True) is True
    assert facade._cic_is_weekend(datetime(2026, 7, 18, 9, 0)) is True
    assert facade._cic_is_weekend(datetime(2026, 7, 20, 9, 0)) is False
    assert facade._cic_v40_bool("aktif") is True
    assert facade._cic_v40_bool("pasif") is False
    assert facade._cic_v45_norm("Çanakkale Şehitleri") == "canakkalesehitleri"
    assert facade._cic_v45_norm_name("  Gülsen   Özden ") == "gulsen ozden"
    assert facade._cic_v45_bool("Evet") is True
    assert facade._cic_v45_bool("Hayır") is False
    assert facade._cic_v45_header_key("Doğum Tarihi") == "birth_date"


def test_json_and_date_helpers_keep_behavior() -> None:
    payload = {"şehir": "Çanakkale", "aktif": True}
    dumped = facade._dumps_json(payload)
    assert json.loads(dumped) == payload
    assert "Çanakkale" in dumped
    assert facade._cic_v40_today(date(2026, 7, 20)) == date(2026, 7, 20)
    assert facade._cic_v45_parse_date("31.12.2024") == date(2024, 12, 31)
