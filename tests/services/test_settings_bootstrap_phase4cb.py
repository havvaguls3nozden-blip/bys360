from __future__ import annotations

from app.services.settings import bootstrap


def test_build_runtime_settings_snapshot_masks_and_skips_blank_keys() -> None:
    values = {
        "   ": "ignored",
        " custom_secret ": "secret-value",
        "site_name": "BYS360",
        "api_token": "token-value",
    }

    definitions = [
        {
            "key": "custom_secret",
            "sensitive": True,
        },
        {
            "key": "site_name",
            "sensitive": False,
        },
    ]

    assert bootstrap.build_runtime_settings_snapshot(
        values,
        definitions,
    ) == {
        "custom_secret": "********",
        "site_name": "BYS360",
        "api_token": "********",
    }


def test_build_runtime_settings_snapshot_preserves_values_when_masking_disabled() -> None:
    values = {
        " password ": "raw-password",
        "site_name": "BYS360",
    }

    definitions = [
        {
            "key": "password",
            "sensitive": True,
        },
    ]

    assert bootstrap.build_runtime_settings_snapshot(
        values,
        definitions,
        mask_sensitive=False,
    ) == {
        "password": "raw-password",
        "site_name": "BYS360",
    }


def test_merge_defaults_normalizes_overrides_and_skips_blank_keys() -> None:
    defaults = {
        "site_name": "Default",
        "theme": "light",
    }

    overrides = {
        " site_name ": "BYS360",
        " locale ": "tr",
        "   ": "ignored",
    }

    assert bootstrap.merge_defaults(
        defaults,
        overrides,
    ) == {
        "site_name": "BYS360",
        "theme": "light",
        "locale": "tr",
    }

    assert defaults == {
        "site_name": "Default",
        "theme": "light",
    }


def test_merge_defaults_accepts_empty_inputs() -> None:
    assert bootstrap.merge_defaults(
        {},
        {},
    ) == {}

    assert bootstrap.merge_defaults(
        None,
        None,
    ) == {}
