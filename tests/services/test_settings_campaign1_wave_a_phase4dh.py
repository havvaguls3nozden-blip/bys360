from __future__ import annotations

import logging
from types import SimpleNamespace

import app.services.settings.change_logs as change_logs
import app.services.settings.ui_panel as ui_panel


class _Expr:
    def __or__(self, other):
        return self

    def __and__(self, other):
        return self


class _Field:
    def __init__(self, name):
        self.name = name

    def desc(self):
        return ("desc", self.name)

    def __eq__(self, other):
        return _Expr()

    def is_(self, other):
        return _Expr()

    def in_(self, values):
        return _Expr()


class _Query:
    def __init__(
        self,
        rows,
        *,
        fail_order=False,
    ):
        self.rows = list(rows)
        self.fail_order = fail_order
        self.calls = []

    def order_by(self, *args):
        self.calls.append(
            ("order_by", args)
        )

        if self.fail_order:
            raise RuntimeError(
                "query failure"
            )

        return self

    def filter(self, *args):
        self.calls.append(
            ("filter", args)
        )
        return self

    def limit(self, value):
        self.calls.append(
            ("limit", value)
        )
        return self

    def all(self):
        self.calls.append(
            ("all", None)
        )
        return list(self.rows)


class _LogModel:
    created_at = _Field("created_at")
    id = _Field("id")
    target_user_id = _Field(
        "target_user_id"
    )
    change_scope = _Field(
        "change_scope"
    )
    query = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _install_ui(
    monkeypatch,
    *,
    snapshot,
    phases,
):
    monkeypatch.setattr(
        ui_panel,
        (
            "build_settings_"
            "refactor_quality_snapshot"
        ),
        lambda: snapshot,
    )

    monkeypatch.setattr(
        ui_panel,
        (
            "get_settings_"
            "refactor_phase_sequence"
        ),
        lambda: phases,
    )


def _install_log_query(
    monkeypatch,
    query,
):
    _LogModel.query = query

    monkeypatch.setattr(
        change_logs,
        "SettingsChangeLog",
        _LogModel,
    )


def test_ui_helpers_cover_conversion_and_status_paths():
    assert ui_panel._as_int("12") == 12
    assert ui_panel._as_int(None) == 0

    assert (
        ui_panel._as_int(
            [1],
            default=7,
        )
        == 7
    )

    assert (
        ui_panel._truth_label(
            True,
            yes="yes",
            no="no",
        )
        == "yes"
    )

    assert (
        ui_panel._truth_label(
            False,
            yes="yes",
            no="no",
        )
        == "no"
    )

    assert (
        ui_panel._status_class(
            "tamamlandi"
        )
        == "ok"
    )

    assert (
        ui_panel._status_class(
            "sirada"
        )
        == "pending"
    )

    assert (
        ui_panel._status_class(
            "other"
        )
        == "warn"
    )


def test_ui_panel_builds_healthy_general_context(
    monkeypatch,
):
    _install_ui(
        monkeypatch,
        snapshot={
            "ok": True,
            "module_states": [
                {
                    "name": "one",
                    "available": True,
                },
            ],
        },
        phases=[
            {
                "phase": "done",
                "status": "tamamland\u0131",
            },
            {
                "phase": "active",
                "status": "aktif",
            },
            {
                "phase": "next",
                "status": "s\u0131rada",
            },
            {
                "phase": "other",
                "status": "unknown",
            },
        ],
    )

    result = (
        ui_panel
        .build_settings_ui_diagnostics_panel(
            foundation_context={
                "stats": {
                    "system_total": "2",
                    "module_total": "3",
                    "role_total": "4",
                    "unit_profile_total": "5",
                    "history_total": "6",
                },
                "recent_change_logs": [],
            },
        )
    )

    assert result["ok"] is True
    assert result["service_ok"] is True
    assert result["db_ready"] is True

    assert (
        result["completed_phase_count"]
        == 1
    )

    assert (
        result["active_phase"]["phase"]
        == "active"
    )

    assert (
        result["next_phase_label"]
        == "next"
    )

    assert (
        result["summary"]["system_total"]
        == 2
    )

    assert (
        result["summary"]["module_total"]
        == 3
    )

    assert [
        item["status_class"]
        for item in result[
            "phase_sequence"
        ]
    ] == [
        "ok",
        "ok",
        "pending",
        "warn",
    ]

    assert (
        result["health_cards"][3][
            "state"
        ]
        == "pending"
    )


def test_ui_panel_builds_selected_problem_context(
    monkeypatch,
):
    _install_ui(
        monkeypatch,
        snapshot={
            "ok": True,
            "module_states": [
                {
                    "name": "missing",
                    "available": False,
                },
            ],
        },
        phases=[
            {
                "phase": "done",
                "status": "tamamland\u0131",
            },
        ],
    )

    result = (
        ui_panel
        .build_settings_ui_diagnostics_panel(
            foundation_context={
                "missing_tables": [
                    "table_x"
                ],
                "recent_change_logs": [],
            },
            profile_context={
                "recent_change_logs": [
                    "log-1"
                ],
            },
            selected_user=SimpleNamespace(
                id=7
            ),
        )
    )

    assert result["ok"] is False
    assert result["service_ok"] is False
    assert result["db_ready"] is False

    assert len(
        result["problem_modules"]
    ) == 1

    assert result["active_phase"] == {}
    assert result["next_phases"] == []

    assert (
        result["health_cards"][0][
            "state"
        ]
        == "warn"
    )

    assert (
        result["health_cards"][1][
            "state"
        ]
        == "warn"
    )

    assert (
        result["health_cards"][3][
            "state"
        ]
        == "ok"
    )


def test_change_log_rollback_and_table_paths(
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
        change_logs,
        "db",
        fake_db,
    )

    change_logs._safe_rollback()

    assert rollback_calls == [
        "rollback"
    ]

    class _Inspector:
        def has_table(self, name):
            return name == "present"

    monkeypatch.setattr(
        change_logs,
        "inspect",
        lambda engine: _Inspector(),
    )

    assert (
        change_logs._table_exists(
            "present"
        )
        is True
    )

    assert (
        change_logs._table_exists(
            "missing"
        )
        is False
    )

    safe_calls = []

    with monkeypatch.context() as scoped:
        scoped.setattr(
            change_logs,
            "_safe_rollback",
            lambda: safe_calls.append(
                "safe"
            ),
        )

        scoped.setattr(
            change_logs,
            "inspect",
            lambda engine: (
                (_ for _ in ()).throw(
                    RuntimeError("inspect")
                )
            ),
        )

        assert (
            change_logs._table_exists(
                "broken"
            )
            is False
        )

    assert safe_calls == ["safe"]

    messages = []

    fake_db.session.rollback = (
        lambda: (
            (_ for _ in ()).throw(
                RuntimeError("rollback")
            )
        )
    )

    with monkeypatch.context() as scoped:
        scoped.setattr(
            logging,
            "getLogger",
            lambda *args, **kwargs: (
                SimpleNamespace(
                    exception=lambda message: (
                        messages.append(
                            message
                        )
                    ),
                )
            ),
        )

        change_logs._safe_rollback()

    assert len(messages) == 1


def test_change_log_serialization_paths(
    monkeypatch,
):
    assert (
        change_logs
        .serialize_settings_state(None)
        is None
    )

    encoded = (
        change_logs
        .serialize_settings_state(
            {
                "b": 2,
                "a": 1,
            }
        )
    )

    assert encoded == (
        '{"a": 1, "b": 2}'
    )

    assert (
        change_logs
        .deserialize_settings_state(None)
        is None
    )

    assert (
        change_logs
        .deserialize_settings_state(
            encoded
        )
        == {
            "a": 1,
            "b": 2,
        }
    )

    messages = []

    with monkeypatch.context() as scoped:
        scoped.setattr(
            logging,
            "getLogger",
            lambda *args, **kwargs: (
                SimpleNamespace(
                    exception=lambda message: (
                        messages.append(
                            message
                        )
                    ),
                )
            ),
        )

        assert (
            change_logs
            .deserialize_settings_state(
                "{"
            )
            is None
        )

    assert len(messages) == 1


def test_create_change_log_handles_missing_and_present_table(
    monkeypatch,
):
    monkeypatch.setattr(
        change_logs,
        "_table_exists",
        lambda name: False,
    )

    common = {
        "actor_user_id": 1,
        "change_scope": (
            "system_settings"
        ),
        "action_type": "save",
        "summary": "summary",
        "previous_state": {
            "old": 1
        },
        "new_state": {
            "new": 2
        },
    }

    assert (
        change_logs
        .create_settings_change_log(
            **common
        )
        is None
    )

    added = []

    monkeypatch.setattr(
        change_logs,
        "_table_exists",
        lambda name: True,
    )

    monkeypatch.setattr(
        change_logs,
        "SettingsChangeLog",
        _LogModel,
    )

    monkeypatch.setattr(
        change_logs,
        "db",
        SimpleNamespace(
            session=SimpleNamespace(
                add=added.append
            ),
        ),
    )

    row = (
        change_logs
        .create_settings_change_log(
            **common,
            target_user_id=9,
            target_role_name=(
                " ADMIN "
            ),
            target_unit_name=(
                " Unit "
            ),
            reverted_from_log_id=4,
            is_rollback=True,
        )
    )

    assert row is added[0]

    assert (
        row.target_role_name
        == "admin"
    )

    assert (
        row.target_unit_name
        == "Unit"
    )

    assert (
        row.previous_state_json
        == '{"old": 1}'
    )

    assert (
        row.new_state_json
        == '{"new": 2}'
    )

    assert row.is_rollback is True


def test_list_recent_logs_without_target_and_missing_table(
    monkeypatch,
):
    monkeypatch.setattr(
        change_logs,
        "_table_exists",
        lambda name: False,
    )

    assert (
        change_logs
        .list_recent_settings_change_logs()
        == []
    )

    query = _Query(
        [
            "row-1",
            "row-2",
        ]
    )

    _install_log_query(
        monkeypatch,
        query,
    )

    monkeypatch.setattr(
        change_logs,
        "_table_exists",
        lambda name: True,
    )

    result = (
        change_logs
        .list_recent_settings_change_logs(
            limit=2
        )
    )

    assert result == [
        "row-1",
        "row-2",
    ]

    assert [
        item[0]
        for item in query.calls
    ] == [
        "order_by",
        "limit",
        "all",
    ]


def test_list_recent_logs_target_filter_and_failure(
    monkeypatch,
):
    query = _Query(
        ["target-row"]
    )

    _install_log_query(
        monkeypatch,
        query,
    )

    monkeypatch.setattr(
        change_logs,
        "_table_exists",
        lambda name: True,
    )

    result = (
        change_logs
        .list_recent_settings_change_logs(
            limit=3,
            target_user_id=7,
        )
    )

    assert result == [
        "target-row"
    ]

    assert [
        item[0]
        for item in query.calls
    ] == [
        "order_by",
        "filter",
        "limit",
        "all",
    ]

    broken_query = _Query(
        [],
        fail_order=True,
    )

    _install_log_query(
        monkeypatch,
        broken_query,
    )

    rollback_calls = []

    monkeypatch.setattr(
        change_logs,
        "_safe_rollback",
        lambda: rollback_calls.append(
            "rollback"
        ),
    )

    assert (
        change_logs
        .list_recent_settings_change_logs()
        == []
    )

    assert rollback_calls == [
        "rollback"
    ]
