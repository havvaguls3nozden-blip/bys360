from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any, cast

import app.services.settings.diagnostics as diagnostics
import app.services.settings.foundation_access as foundation
from app.models.settings_models import SettingsChangeLog


class _Inspector:
    def __init__(self, existing):
        self.existing = set(existing)

    def has_table(self, name):
        return name in self.existing


class _CountQuery:
    def __init__(
        self,
        count_value=0,
        *,
        fail=False,
    ):
        self.count_value = count_value
        self.fail = fail

    def count(self):
        if self.fail:
            raise RuntimeError(
                "count"
            )

        return self.count_value

    def with_entities(self, column):
        if self.fail:
            raise RuntimeError(
                "entities"
            )

        return self

    def distinct(self):
        return self


class _RecentField:
    def desc(self):
        return self


class _RecentQuery:
    def __init__(
        self,
        rows=(),
        *,
        fail=False,
    ):
        self.rows = list(rows)
        self.fail = fail
        self.limit_value = None

    def order_by(self, *args):
        if self.fail:
            raise RuntimeError(
                "recent"
            )

        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def all(self):
        return list(self.rows)


class _SeedQuery:
    def __init__(
        self,
        rows=(),
        *,
        fail=False,
    ):
        self.rows = list(rows)
        self.fail = fail
        self.filters = []

    def filter_by(self, **kwargs):
        if self.fail:
            raise RuntimeError(
                "query"
            )

        self.filters.append(kwargs)
        return self

    def all(self):
        if self.fail:
            raise RuntimeError(
                "query"
            )

        return list(self.rows)


class _SeedRoleModel:
    query = _SeedQuery()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _SeedSystemModel:
    query = _SeedQuery()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _SeedModuleModel:
    query = _SeedQuery()

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _Session:
    def __init__(self):
        self.added = []
        self.commit_calls = 0

    def add(self, row):
        self.added.append(row)

    def commit(self):
        self.commit_calls += 1


def test_diagnostics_safe_helpers(
    monkeypatch,
):
    rollback_calls = []

    fake_db = SimpleNamespace(
        engine=object(),
        session=SimpleNamespace(
            rollback=lambda: (
                rollback_calls.append(
                    "rollback"
                )
            ),
        ),
    )

    monkeypatch.setattr(
        diagnostics,
        "db",
        fake_db,
    )

    diagnostics._safe_rollback()

    assert rollback_calls == [
        "rollback"
    ]

    logged = []

    fake_db.session.rollback = (
        lambda: (
            (_ for _ in ()).throw(
                RuntimeError(
                    "rollback"
                )
            )
        )
    )

    with monkeypatch.context() as scoped:
        scoped.setattr(
            diagnostics.logging,
            "getLogger",
            lambda *args, **kwargs: (
                SimpleNamespace(
                    exception=lambda message: (
                        logged.append(
                            message
                        )
                    )
                )
            ),
        )

        diagnostics._safe_rollback()

    assert len(logged) == 1

    monkeypatch.setattr(
        diagnostics,
        "inspect",
        lambda engine: _Inspector(
            {
                "present"
            }
        ),
    )

    assert (
        diagnostics._table_exists(
            "present"
        )
        is True
    )

    assert (
        diagnostics._table_exists(
            "missing"
        )
        is False
    )

    safe_calls = []

    monkeypatch.setattr(
        diagnostics,
        "_safe_rollback",
        lambda: safe_calls.append(
            "safe"
        ),
    )

    monkeypatch.setattr(
        diagnostics,
        "inspect",
        lambda engine: (
            (_ for _ in ()).throw(
                RuntimeError(
                    "inspect"
                )
            )
        ),
    )

    assert (
        diagnostics._table_exists(
            "broken"
        )
        is False
    )

    ok_model = SimpleNamespace(
        query=_CountQuery(7)
    )

    fail_model = SimpleNamespace(
        query=_CountQuery(
            fail=True
        )
    )

    assert (
        diagnostics._safe_count(
            ok_model
        )
        == 7
    )

    assert (
        diagnostics._safe_count(
            fail_model
        )
        == 0
    )

    assert (
        diagnostics
        ._safe_distinct_count(
            ok_model,
            object(),
        )
        == 7
    )

    assert (
        diagnostics
        ._safe_distinct_count(
            fail_model,
            object(),
        )
        == 0
    )

    assert safe_calls == [
        "safe",
        "safe",
        "safe",
    ]


def test_diagnostics_normalize_and_table_health(
    monkeypatch,
):
    assert (
        diagnostics._normalize_menu_keys(
            [
                None,
                "",
                " a ",
                "a",
                "b",
            ]
        )
        == [
            "a",
            "b",
        ]
    )

    monkeypatch.setattr(
        diagnostics,
        "_table_exists",
        lambda name: (
            name != "module_settings"
        ),
    )

    monkeypatch.setattr(
        diagnostics,
        "_safe_count",
        lambda model: 5,
    )

    result = (
        diagnostics
        .build_settings_table_health()
    )

    assert result["ready"] is False

    assert result[
        "missing_tables"
    ] == [
        "module_settings"
    ]

    assert len(
        result["tables"]
    ) == len(
        diagnostics.CORE_SETTINGS_TABLES
    )

    missing = next(
        item
        for item in result["tables"]
        if item["table_name"]
        == "module_settings"
    )

    present = next(
        item
        for item in result["tables"]
        if item["table_name"]
        == "system_settings"
    )

    assert missing == {
        "table_name": (
            "module_settings"
        ),
        "exists": False,
        "row_count": 0,
        "status": "missing",
    }

    assert present["exists"] is True
    assert present["row_count"] == 5
    assert present["status"] == "ok"


def test_diagnostics_menu_registry_health_success_and_fallback(
    monkeypatch,
):
    monkeypatch.setattr(
        diagnostics,
        "flatten_menu_definitions",
        lambda: [
            {
                "key": "messages"
            },
            {
                "key": "notifications"
            },
            {
                "key": "surveys"
            },
            {
                "key": (
                    "performance_reports"
                )
            },
            {
                "key": "removed"
            },
            {
                "key": "messages"
            },
            "ignored",
        ],
    )

    monkeypatch.setattr(
        diagnostics,
        "is_removed_menu_key",
        lambda key: key == "removed",
    )

    monkeypatch.setattr(
        diagnostics,
        "ROLE_MENU_DEFAULTS",
        {
            "admin": {},
            "user": {},
        },
    )

    monkeypatch.setattr(
        diagnostics,
        "_table_exists",
        lambda name: name
        in {
            "role_menu_defaults",
            "user_menu_permissions",
        },
    )

    monkeypatch.setattr(
        diagnostics,
        "_safe_distinct_count",
        lambda model, column: 3,
    )

    result = (
        diagnostics
        .build_menu_registry_health()
    )

    assert result["menu_total"] == 5
    assert result["live_menu_total"] == 4

    assert result[
        "removed_menu_keys"
    ] == [
        "removed"
    ]

    assert (
        result["role_default_total"]
        == 2
    )

    assert (
        result["role_profile_count"]
        == 3
    )

    assert (
        result["unit_profile_count"]
        == 0
    )

    assert (
        result[
            "user_override_user_count"
        ]
        == 3
    )

    assert all(
        result[
            "core_menu_present"
        ].values()
    )

    monkeypatch.setattr(
        diagnostics,
        "flatten_menu_definitions",
        lambda: (
            (_ for _ in ()).throw(
                RuntimeError(
                    "registry"
                )
            )
        ),
    )

    monkeypatch.setattr(
        diagnostics,
        "_table_exists",
        lambda name: (
            name
            == "unit_menu_profiles"
        ),
    )

    fallback = (
        diagnostics
        .build_menu_registry_health()
    )

    assert fallback["menu_total"] == 0

    assert (
        fallback["role_profile_count"]
        == 0
    )

    assert (
        fallback["unit_profile_count"]
        == 3
    )

    assert (
        fallback[
            "user_override_user_count"
        ]
        == 0
    )

    assert not any(
        fallback[
            "core_menu_present"
        ].values()
    )


def test_diagnostics_activity_and_context(
    monkeypatch,
):
    created = datetime(
        2026,
        7,
        15,
        12,
        0,
        0,
    )

    row = SimpleNamespace(
        id=1,
        change_scope=(
            "system_settings"
        ),
        action_type="save",
        summary="saved",
        actor_user_id=2,
        target_user_id=3,
        target_role_name="admin",
        target_unit_name="unit",
        is_rollback=True,
        reverted_from_log_id=4,
        created_at=created,
    )

    empty_time_row = SimpleNamespace(
        created_at=None
    )

    assert (
        diagnostics._log_to_dict(
            cast(SettingsChangeLog, row)
        )["created_at"]
        == created.isoformat()
    )

    assert (
        diagnostics._log_to_dict(
            cast(SettingsChangeLog, empty_time_row)
        )["created_at"]
        is None
    )

    monkeypatch.setattr(
        diagnostics,
        "_table_exists",
        lambda name: False,
    )

    assert (
        diagnostics
        .list_settings_recent_activity()
        == []
    )

    # Dynamically-built via type(); has no fixed attribute contract for
    # mypy to see, matching the ad hoc namespaces used throughout this file.
    fake_model: Any = type(
        "LogModel",
        (),
        {
            "id": _RecentField(),
            "query": _RecentQuery(
                [
                    row
                ]
            ),
        },
    )

    monkeypatch.setattr(
        diagnostics,
        "SettingsChangeLog",
        fake_model,
    )

    monkeypatch.setattr(
        diagnostics,
        "_table_exists",
        lambda name: True,
    )

    assert (
        diagnostics
        .list_settings_recent_activity(
            100
        )[0]["id"]
        == 1
    )

    assert (
        fake_model.query.limit_value
        == 50
    )

    broken_model = type(
        "BrokenLog",
        (),
        {
            "id": _RecentField(),
            "query": _RecentQuery(
                fail=True
            ),
        },
    )

    monkeypatch.setattr(
        diagnostics,
        "SettingsChangeLog",
        broken_model,
    )

    safe_calls = []

    monkeypatch.setattr(
        diagnostics,
        "_safe_rollback",
        lambda: safe_calls.append(
            "safe"
        ),
    )

    assert (
        diagnostics
        .list_settings_recent_activity(
            0
        )
        == []
    )

    assert safe_calls == [
        "safe"
    ]

    monkeypatch.setattr(
        diagnostics,
        "build_settings_table_health",
        lambda: {
            "ready": True,
            "missing_tables": [],
        },
    )

    monkeypatch.setattr(
        diagnostics,
        "build_menu_registry_health",
        lambda: {
            "live_menu_total": 4,
            "removed_menu_total": 1,
            "core_menu_present": {
                "messages": True,
                "surveys": True,
            },
        },
    )

    monkeypatch.setattr(
        diagnostics,
        "list_settings_recent_activity",
        lambda limit: [
            "log"
        ],
    )

    healthy = (
        diagnostics
        .build_settings_diagnostics_context(
            include_recent_logs=True,
            recent_limit=5,
        )
    )

    assert healthy["ready"] is True

    assert healthy[
        "warning_codes"
    ] == []

    assert healthy[
        "recent_activity"
    ] == [
        "log"
    ]

    monkeypatch.setattr(
        diagnostics,
        "build_settings_table_health",
        lambda: {
            "ready": False,
            "missing_tables": [
                "x"
            ],
        },
    )

    monkeypatch.setattr(
        diagnostics,
        "build_menu_registry_health",
        lambda: {
            "live_menu_total": 0,
            "removed_menu_total": 0,
            "core_menu_present": {
                "messages": False,
                "surveys": False,
            },
        },
    )

    unhealthy = (
        diagnostics
        .build_settings_diagnostics_context(
            include_recent_logs=False,
        )
    )

    assert unhealthy["ready"] is False

    assert unhealthy[
        "recent_activity"
    ] == []

    assert unhealthy[
        "warning_codes"
    ] == [
        "settings_tables_missing",
        "live_menu_registry_empty",
        "messages_menu_missing",
        "surveys_menu_missing",
    ]


def test_foundation_live_definition_filtering():
    items = [
        {
            "module_key": "",
            "setting_key": "x",
        },
        {
            "module_key": "portal",
            "setting_key": "",
        },
        {
            "module_key": "dead",
            "setting_key": "x",
        },
        {
            "module_key": " portal ",
            "setting_key": " one ",
        },
        {
            "module_key": "portal",
            "setting_key": "one",
        },
        {
            "module_key": "portal",
            "setting_key": "two",
        },
    ]

    result = (
        foundation
        .iter_live_module_setting_definitions(
            items,
            lambda key: (
                key == "portal"
            ),
        )
    )

    assert result == [
        items[3],
        items[5],
    ]


def test_foundation_seed_missing_tables():
    result = (
        foundation
        .ensure_settings_phase1_seeded_handler(
            updated_by_user_id=1,
            table_exists=lambda name: (
                name != "module_settings"
            ),
            flatten_menu_definitions_func=(
                lambda: []
            ),
            filter_live_menu_keys=(
                lambda keys: list(keys)
            ),
            static_role_default_menu_keys_func=(
                lambda role: set()
            ),
            role_menu_defaults={},
            role_menu_default_model=(
                _SeedRoleModel
            ),
            system_setting_model=(
                _SeedSystemModel
            ),
            module_setting_model=(
                _SeedModuleModel
            ),
            db_session=_Session(),
            system_definitions=[],
            iter_live_module_setting_definitions_func=(
                lambda: []
            ),
            value_to_storage=(
                lambda value, kind: (
                    str(value)
                )
            ),
            safe_rollback=lambda: None,
        )
    )

    assert result["ok"] is False

    assert result[
        "missing_tables"
    ] == [
        "module_settings"
    ]


def test_foundation_seed_success_covers_insert_update_and_existing():
    update_row = SimpleNamespace(
        menu_key="update",
        source_type="seed",
        is_visible=False,
        updated_by_user_id=None,
    )

    keep_row = SimpleNamespace(
        menu_key="keep",
        source_type="manual",
        is_visible=False,
        updated_by_user_id=None,
    )

    _SeedRoleModel.query = (
        _SeedQuery(
            [
                update_row,
                keep_row,
            ]
        )
    )

    _SeedSystemModel.query = (
        _SeedQuery(
            [
                SimpleNamespace(
                    setting_key=(
                        "existing"
                    )
                )
            ]
        )
    )

    _SeedModuleModel.query = (
        _SeedQuery(
            [
                SimpleNamespace(
                    module_key="portal",
                    setting_key=(
                        "existing"
                    ),
                )
            ]
        )
    )

    session = _Session()

    result = (
        foundation
        .ensure_settings_phase1_seeded_handler(
            updated_by_user_id=9,
            table_exists=(
                lambda name: True
            ),
            flatten_menu_definitions_func=(
                lambda: [
                    {
                        "key": "new"
                    },
                    {
                        "key": "update"
                    },
                    {
                        "key": "keep"
                    },
                ]
            ),
            filter_live_menu_keys=(
                lambda keys: list(keys)
            ),
            static_role_default_menu_keys_func=(
                lambda role: {
                    "new",
                    "update",
                }
            ),
            role_menu_defaults={
                "admin": {}
            },
            role_menu_default_model=(
                _SeedRoleModel
            ),
            system_setting_model=(
                _SeedSystemModel
            ),
            module_setting_model=(
                _SeedModuleModel
            ),
            db_session=session,
            system_definitions=[
                {
                    "setting_key": "new",
                    "group_key": (
                        "general"
                    ),
                    "label": "New",
                    "default": 1,
                    "value_type": "int",
                },
                {
                    "setting_key": (
                        "existing"
                    ),
                    "group_key": (
                        "general"
                    ),
                    "label": "Existing",
                    "default": 2,
                    "value_type": "int",
                },
            ],
            iter_live_module_setting_definitions_func=(
                lambda: [
                    {
                        "module_key": (
                            "portal"
                        ),
                        "setting_key": (
                            "new"
                        ),
                        "label": "New",
                        "default": True,
                        "value_type": (
                            "bool"
                        ),
                    },
                    {
                        "module_key": (
                            "portal"
                        ),
                        "setting_key": (
                            "existing"
                        ),
                        "label": (
                            "Existing"
                        ),
                        "default": False,
                        "value_type": (
                            "bool"
                        ),
                    },
                ]
            ),
            value_to_storage=(
                lambda value, kind: (
                    f"{kind}:{value}"
                )
            ),
            safe_rollback=lambda: None,
        )
    )

    assert result == {
        "ok": True,
        "seeded_role_defaults": 1,
        "seeded_system_settings": 1,
        "seeded_module_settings": 1,
    }

    assert session.commit_calls == 1
    assert len(session.added) == 3
    assert update_row.is_visible is True

    assert (
        update_row.updated_by_user_id
        == 9
    )

    assert keep_row.is_visible is False


def test_foundation_context_success():
    system_row = SimpleNamespace(
        setting_key="existing",
        value_text="stored-system",
    )

    module_row = SimpleNamespace(
        module_key="portal",
        setting_key="existing",
        value_text="stored-module",
    )

    system_model = SimpleNamespace(
        query=_SeedQuery(
            [
                system_row
            ]
        )
    )

    module_model = SimpleNamespace(
        query=_SeedQuery(
            [
                module_row
            ]
        )
    )

    result = (
        foundation
        .build_settings_foundation_context_handler(
            table_exists=(
                lambda name: True
            ),
            missing_settings_tables=(
                lambda: []
            ),
            system_setting_model=(
                system_model
            ),
            module_setting_model=(
                module_model
            ),
            system_definitions=[
                {
                    "setting_key": (
                        "existing"
                    ),
                    "group_key": (
                        "general"
                    ),
                    "group_label": (
                        "General"
                    ),
                    "value_type": "str",
                },
                {
                    "setting_key": (
                        "defaulted"
                    ),
                    "group_key": (
                        "general"
                    ),
                    "group_label": (
                        "General"
                    ),
                    "group_description": (
                        "Group"
                    ),
                    "default": (
                        "fallback"
                    ),
                    "value_type": "str",
                },
            ],
            iter_live_module_setting_definitions_func=(
                lambda: [
                    {
                        "module_key": (
                            "portal"
                        ),
                        "module_label": (
                            "Portal"
                        ),
                        "setting_key": (
                            "existing"
                        ),
                        "value_type": (
                            "str"
                        ),
                    },
                    {
                        "module_key": (
                            "portal"
                        ),
                        "module_label": (
                            "Portal"
                        ),
                        "module_description": (
                            "Module"
                        ),
                        "setting_key": (
                            "defaulted"
                        ),
                        "default": (
                            "fallback-module"
                        ),
                        "value_type": (
                            "str"
                        ),
                    },
                ]
            ),
            value_to_python=(
                lambda value, kind: (
                    f"{kind}:{value}"
                )
            ),
            build_role_default_snapshot=(
                lambda: cast(list[dict[str, Any]], [
                    "role"
                ])
            ),
            build_unit_profile_snapshot=(
                lambda: cast(list[dict[str, Any]], [
                    "unit"
                ])
            ),
            list_recent_settings_change_logs_func=(
                lambda: [
                    "log"
                ]
            ),
            role_menu_defaults={
                "admin": {}
            },
            safe_rollback=lambda: None,
        )
    )

    assert result["db_ready"] is True

    assert (
        result["system_groups"][0]
        ["rows"][0]["current_value"]
        == "str:stored-system"
    )

    assert (
        result["system_groups"][0]
        ["rows"][1]["current_value"]
        == "str:fallback"
    )

    assert (
        result["module_groups"][0]
        ["rows"][0]["current_value"]
        == "str:stored-module"
    )

    assert (
        result["module_groups"][0]
        ["rows"][1]["current_value"]
        == "str:fallback-module"
    )

    assert result["stats"] == {
        "system_total": 2,
        "module_total": 2,
        "module_group_total": 1,
        "role_total": 1,
        "unit_profile_total": 1,
        "history_total": 1,
    }


def test_foundation_context_query_failures():
    safe_calls = []

    failing_model = SimpleNamespace(
        query=_SeedQuery(
            fail=True
        )
    )

    result = (
        foundation
        .build_settings_foundation_context_handler(
            table_exists=(
                lambda name: True
            ),
            missing_settings_tables=(
                lambda: [
                    "other"
                ]
            ),
            system_setting_model=(
                failing_model
            ),
            module_setting_model=(
                failing_model
            ),
            system_definitions=[
                {
                    "setting_key": (
                        "defaulted"
                    ),
                    "group_key": (
                        "general"
                    ),
                    "group_label": (
                        "General"
                    ),
                    "default": (
                        "system-default"
                    ),
                    "value_type": (
                        "str"
                    ),
                },
            ],
            iter_live_module_setting_definitions_func=(
                lambda: [
                    {
                        "module_key": (
                            "portal"
                        ),
                        "module_label": (
                            "Portal"
                        ),
                        "setting_key": (
                            "defaulted"
                        ),
                        "default": (
                            "module-default"
                        ),
                        "value_type": (
                            "str"
                        ),
                    },
                ]
            ),
            value_to_python=(
                lambda value, kind: value
            ),
            build_role_default_snapshot=(
                lambda: []
            ),
            build_unit_profile_snapshot=(
                lambda: []
            ),
            list_recent_settings_change_logs_func=(
                lambda: []
            ),
            role_menu_defaults={},
            safe_rollback=(
                lambda: safe_calls.append(
                    "safe"
                )
            ),
        )
    )

    assert safe_calls == [
        "safe",
        "safe",
    ]

    assert result["db_ready"] is False

    assert (
        result["system_groups"][0]
        ["rows"][0]["current_value"]
        == "system-default"
    )

    assert (
        result["module_groups"][0]
        ["rows"][0]["current_value"]
        == "module-default"
    )


def test_foundation_context_tables_absent_and_empty_loops():
    result = (
        foundation
        .build_settings_foundation_context_handler(
            table_exists=(
                lambda name: False
            ),
            missing_settings_tables=(
                lambda: [
                    "system_settings",
                    "module_settings",
                ]
            ),
            system_setting_model=(
                SimpleNamespace(
                    query=_SeedQuery(
                        fail=True
                    )
                )
            ),
            module_setting_model=(
                SimpleNamespace(
                    query=_SeedQuery(
                        fail=True
                    )
                )
            ),
            system_definitions=[],
            iter_live_module_setting_definitions_func=(
                lambda: []
            ),
            value_to_python=(
                lambda value, kind: value
            ),
            build_role_default_snapshot=(
                lambda: []
            ),
            build_unit_profile_snapshot=(
                lambda: []
            ),
            list_recent_settings_change_logs_func=(
                lambda: []
            ),
            role_menu_defaults={},
            safe_rollback=lambda: None,
        )
    )

    assert result[
        "system_groups"
    ] == []

    assert result[
        "module_groups"
    ] == []

    assert result["db_ready"] is False
