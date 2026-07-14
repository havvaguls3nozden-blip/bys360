from __future__ import annotations

from app.services.settings.definitions import (
    build_definition,
    group_definitions,
    index_definitions,
)


def test_build_definition_returns_existing_identity() -> None:
    existing = build_definition(
        {
            "key": "existing_key",
            "label": "Existing",
        }
    )

    assert build_definition(existing) is existing


def test_build_definition_maps_explicit_fields() -> None:
    definition = build_definition(
        {
            "key": "portal_title",
            "label": "  Portal Title  ",
            "value_type": "  bool  ",
            "default": "yes",
            "group": "  interface  ",
            "description": "  Visible portal title  ",
            "sensitive": 1,
            "editable": 0,
            "required": "yes",
        }
    )

    assert definition.key == "portal_title"
    assert definition.label == "Portal Title"
    assert definition.value_type == "bool"
    assert definition.default == "yes"
    assert definition.group == "interface"
    assert definition.description == "Visible portal title"
    assert definition.sensitive is True
    assert definition.editable is False
    assert definition.required is True


def test_build_definition_uses_aliases_and_defaults() -> None:
    definition = build_definition(
        {
            "key": "max_items",
            "label": "",
            "type": "  int  ",
            "default": 12,
            "group": "",
            "description": None,
            "sensitive": False,
            "editable": False,
            "required": False,
        }
    )

    assert definition.key == "max_items"
    assert definition.label == "max_items"
    assert definition.value_type == "int"
    assert definition.default == 12
    assert definition.group == "general"
    assert definition.description == ""
    assert definition.sensitive is False
    assert definition.editable is False
    assert definition.required is False


def test_index_definitions_skips_empty_keys_and_last_duplicate_wins() -> None:
    indexed = index_definitions(
        [
            {
                "key": "",
                "label": "Ignored",
            },
            {
                "key": "alpha",
                "label": "First Alpha",
            },
            {
                "key": "beta",
                "label": "Beta",
            },
            {
                "key": "alpha",
                "label": "Last Alpha",
            },
        ]
    )

    assert set(indexed) == {"alpha", "beta"}
    assert indexed["alpha"].label == "Last Alpha"
    assert indexed["beta"].label == "Beta"


def test_group_definitions_applies_general_group_and_sorts() -> None:
    zulu = build_definition(
        {
            "key": "zulu",
            "label": "Zulu",
            "group": "team",
        }
    )
    alpha = build_definition(
        {
            "key": "alpha",
            "label": "alpha",
            "group": "team",
        }
    )
    fallback = build_definition(
        {
            "key": "fallback_key",
            "label": "",
            "group": "",
        }
    )
    bravo = build_definition(
        {
            "key": "bravo_key",
            "label": "Bravo",
            "group": "",
        }
    )

    grouped = group_definitions(
        [
            zulu,
            fallback,
            alpha,
            bravo,
        ]
    )

    assert set(grouped) == {"team", "general"}

    assert [
        definition.key
        for definition in grouped["team"]
    ] == [
        "alpha",
        "zulu",
    ]

    assert [
        definition.key
        for definition in grouped["general"]
    ] == [
        "bravo_key",
        "fallback_key",
    ]


def test_index_and_group_definitions_accept_empty_iterables() -> None:
    assert index_definitions([]) == {}
    assert group_definitions([]) == {}
