from __future__ import annotations

from types import SimpleNamespace

import pytest

import app.services.settings.form_pipeline as pipeline


class _Query:
    def __init__(self, rows):
        self.rows = list(rows)
        self.all_calls = 0

    def all(self):
        self.all_calls += 1
        return list(self.rows)


class _Session:
    def __init__(self):
        self.added = []
        self.commit_calls = 0

    def add(self, row):
        self.added.append(row)

    def commit(self):
        self.commit_calls += 1


class _SystemModel:
    query = _Query([])

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class _ModuleModel:
    query = _Query([])

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _install_models(
    monkeypatch,
    *,
    system_rows=(),
    module_rows=(),
):
    session = _Session()

    _SystemModel.query = _Query(
        system_rows
    )

    _ModuleModel.query = _Query(
        module_rows
    )

    monkeypatch.setattr(
        pipeline,
        "db",
        SimpleNamespace(
            session=session
        ),
    )

    monkeypatch.setattr(
        pipeline,
        "SystemSetting",
        _SystemModel,
    )

    monkeypatch.setattr(
        pipeline,
        "ModuleSetting",
        _ModuleModel,
    )

    return session


def test_form_pipeline_helpers_and_table_contract():
    assert pipeline.FORM_SAVE_PIPELINE_SCOPES == (
        "system_settings",
        "module_settings",
    )

    pipeline._ensure_table(
        "present",
        lambda name: name == "present",
    )

    with pytest.raises(
        RuntimeError,
        match="system_settings",
    ):
        pipeline._ensure_table(
            "system_settings",
            lambda name: False,
        )

    assert (
        pipeline._system_field_name(
            "site.name"
        )
        == "system__site__name"
    )

    assert (
        pipeline._module_field_name(
            "portal",
            "feature.enabled",
        )
        == (
            "module__portal__"
            "feature__enabled"
        )
    )

    assert (
        pipeline._incoming_form_value(
            {
                "feature": "on",
            },
            "feature",
            "bool",
        )
        == "true"
    )

    assert (
        pipeline._incoming_form_value(
            {},
            "feature",
            "bool",
        )
        == "false"
    )

    assert (
        pipeline._incoming_form_value(
            {
                "title": "BYS360",
            },
            "title",
            "text",
        )
        == "BYS360"
    )


def test_save_system_settings_covers_new_changed_and_unchanged(
    monkeypatch,
):
    changed_row = SimpleNamespace(
        setting_key="site.title",
        group_key="old-group",
        label="Old title",
        value_text="old",
        value_type="str",
        description="old description",
        updated_by_user_id=None,
    )

    unchanged_row = SimpleNamespace(
        setting_key="site.mode",
        group_key="general",
        label="Mode",
        value_text="same",
        value_type="str",
        description=None,
        updated_by_user_id=None,
    )

    session = _install_models(
        monkeypatch,
        system_rows=[
            changed_row,
            unchanged_row,
        ],
    )

    table_calls = []

    def table_exists(name):
        table_calls.append(name)
        return True

    snapshots = iter(
        [
            {
                "before": "state",
            },
            {
                "after": "state",
            },
        ]
    )

    storage_calls = []

    def value_to_storage(
        value,
        value_type,
    ):
        storage_calls.append(
            (
                value,
                value_type,
            )
        )

        return str(value)

    change_logs = []

    definitions = [
        {
            "setting_key": (
                "feature.enabled"
            ),
            "group_key": "features",
            "label": "Feature",
            "input_type": "bool",
            "value_type": "bool",
            "description": "Enabled",
        },
        {
            "setting_key": "site.title",
            "group_key": "general",
            "label": "Site title",
            "input_type": "text",
            "value_type": "str",
            "description": (
                "Updated description"
            ),
        },
        {
            "setting_key": "site.mode",
            "group_key": "general",
            "label": "Mode",
            "input_type": "text",
            "value_type": "str",
        },
    ]

    changed = (
        pipeline
        .save_system_settings_from_form_handler(
            {
                (
                    "system__feature__"
                    "enabled"
                ): "on",
                "system__site__title": "new",
                "system__site__mode": "same",
            },
            updated_by_user_id=42,
            table_exists=table_exists,
            system_definitions=definitions,
            value_to_storage=(
                value_to_storage
            ),
            snapshot_system_state=(
                lambda: next(snapshots)
            ),
            create_change_log=(
                lambda **kwargs: (
                    change_logs.append(
                        kwargs
                    )
                )
            ),
        )
    )

    assert changed == 2
    assert table_calls == [
        "system_settings"
    ]

    assert (
        _SystemModel.query.all_calls
        == 1
    )

    assert len(session.added) == 1

    new_row = session.added[0]

    assert isinstance(
        new_row,
        _SystemModel,
    )

    assert (
        new_row.setting_key
        == "feature.enabled"
    )

    assert new_row.value_text == "true"

    assert (
        new_row.updated_by_user_id
        == 42
    )

    assert changed_row.value_text == "new"
    assert (
        changed_row.group_key
        == "general"
    )
    assert (
        changed_row.label
        == "Site title"
    )
    assert (
        changed_row.description
        == "Updated description"
    )
    assert (
        changed_row.updated_by_user_id
        == 42
    )

    assert unchanged_row.value_text == "same"

    assert storage_calls == [
        (
            "true",
            "bool",
        ),
        (
            "new",
            "str",
        ),
        (
            "same",
            "str",
        ),
    ]

    assert session.commit_calls == 1
    assert len(change_logs) == 1

    log = change_logs[0]

    assert log["actor_user_id"] == 42

    assert (
        log["change_scope"]
        == "system_settings"
    )

    assert log["action_type"] == "save"

    assert log["previous_state"] == {
        "before": "state",
    }

    assert log["new_state"] == {
        "after": "state",
    }


def test_save_module_settings_covers_new_changed_and_unchanged(
    monkeypatch,
):
    changed_row = SimpleNamespace(
        module_key="portal",
        setting_key="title",
        label="Old title",
        value_text="old",
        value_type="str",
        description="old description",
        updated_by_user_id=None,
    )

    unchanged_row = SimpleNamespace(
        module_key="portal",
        setting_key="mode",
        label="Mode",
        value_text="same",
        value_type="str",
        description=None,
        updated_by_user_id=None,
    )

    session = _install_models(
        monkeypatch,
        module_rows=[
            changed_row,
            unchanged_row,
        ],
    )

    table_calls = []

    def table_exists(name):
        table_calls.append(name)
        return True

    snapshots = iter(
        [
            {
                "portal": {
                    "before": "state",
                },
            },
            {
                "portal": {
                    "after": "state",
                },
            },
        ]
    )

    storage_calls = []

    def value_to_storage(
        value,
        value_type,
    ):
        storage_calls.append(
            (
                value,
                value_type,
            )
        )

        return str(value)

    change_logs = []

    definitions = [
        {
            "module_key": "portal",
            "setting_key": "enabled",
            "label": "Enabled",
            "input_type": "bool",
            "value_type": "bool",
            "description": "Portal enabled",
        },
        {
            "module_key": "portal",
            "setting_key": "title",
            "label": "Portal title",
            "input_type": "text",
            "value_type": "str",
            "description": (
                "Updated description"
            ),
        },
        {
            "module_key": "portal",
            "setting_key": "mode",
            "label": "Mode",
            "input_type": "text",
            "value_type": "str",
        },
    ]

    changed = (
        pipeline
        .save_module_settings_from_form_handler(
            {
                (
                    "module__portal__"
                    "enabled"
                ): "on",
                (
                    "module__portal__"
                    "title"
                ): "new",
                (
                    "module__portal__"
                    "mode"
                ): "same",
            },
            updated_by_user_id=51,
            table_exists=table_exists,
            iter_live_module_setting_definitions=(
                lambda: definitions
            ),
            value_to_storage=(
                value_to_storage
            ),
            snapshot_module_state=(
                lambda: next(snapshots)
            ),
            create_change_log=(
                lambda **kwargs: (
                    change_logs.append(
                        kwargs
                    )
                )
            ),
        )
    )

    assert changed == 2
    assert table_calls == [
        "module_settings"
    ]

    assert (
        _ModuleModel.query.all_calls
        == 1
    )

    assert len(session.added) == 1

    new_row = session.added[0]

    assert isinstance(
        new_row,
        _ModuleModel,
    )

    assert new_row.module_key == "portal"
    assert new_row.setting_key == "enabled"
    assert new_row.value_text == "true"

    assert (
        new_row.updated_by_user_id
        == 51
    )

    assert changed_row.value_text == "new"
    assert (
        changed_row.label
        == "Portal title"
    )
    assert (
        changed_row.description
        == "Updated description"
    )
    assert (
        changed_row.updated_by_user_id
        == 51
    )

    assert unchanged_row.value_text == "same"

    assert storage_calls == [
        (
            "true",
            "bool",
        ),
        (
            "new",
            "str",
        ),
        (
            "same",
            "str",
        ),
    ]

    assert session.commit_calls == 1
    assert len(change_logs) == 1

    log = change_logs[0]

    assert log["actor_user_id"] == 51

    assert (
        log["change_scope"]
        == "module_settings"
    )

    assert log["action_type"] == "save"

    assert log["previous_state"] == {
        "portal": {
            "before": "state",
        },
    }

    assert log["new_state"] == {
        "portal": {
            "after": "state",
        },
    }
