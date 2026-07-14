from __future__ import annotations

import copy

import pytest

import app.services.settings.final_hardening as target


def _closed_phases() -> list[dict[str, object]]:
    return [
        {
            "phase": index,
            "status": "tamamland\u0131",
        }
        for index in range(4, 13)
    ]


def test_bool_and_as_int_helpers() -> None:
    assert target._bool(True) is True
    assert target._bool(False) is False
    assert target._bool("value") is True
    assert target._bool("") is False

    assert target._as_int("7") == 7
    assert target._as_int(4) == 4
    assert target._as_int(None) == 0

    assert target._as_int(
        "not-an-int",
        default=9,
    ) == 9

    assert target._as_int(
        [],
        default=8,
    ) == 0

    assert target._as_int(
        [1],
        default=8,
    ) == 8


def test_guard_builds_ok_and_control_statuses() -> None:
    ok_guard = target._guard(
        "guard.ok",
        True,
        "OK title",
        "OK detail",
    )

    failed_guard = target._guard(
        "guard.failed",
        False,
        "Failed title",
        "Failed detail",
    )

    assert ok_guard == {
        "code": "guard.ok",
        "ok": True,
        "status": "OK",
        "title": "OK title",
        "detail": "OK detail",
    }

    assert failed_guard == {
        "code": "guard.failed",
        "ok": False,
        "status": "KONTROL",
        "title": "Failed title",
        "detail": "Failed detail",
    }


def test_release_checklist_returns_independent_copies() -> None:
    first = (
        target.get_settings_final_release_checklist()
    )

    second = (
        target.get_settings_final_release_checklist()
    )

    expected = [
        dict(item)
        for item in target.FINAL_HARDENING_GUARDS
    ]

    assert first == expected
    assert second == expected
    assert first is not second

    assert all(
        copied is not original
        for copied, original in zip(
            first,
            target.FINAL_HARDENING_GUARDS,
            strict=True,
        )
    )

    first[0]["title"] = "changed"

    assert second[0]["title"] != "changed"
    assert (
        target.FINAL_HARDENING_GUARDS[0]["title"]
        != "changed"
    )


def test_build_report_success(
    monkeypatch,
) -> None:
    snapshot = {
        "ok": True,
        "module_states": [
            {
                "name": "module_a",
                "available": True,
            },
            {
                "name": "module_b",
                "available": True,
            },
        ],
    }

    phases = _closed_phases()

    monkeypatch.setattr(
        target,
        "build_settings_refactor_quality_snapshot",
        lambda: snapshot,
    )

    monkeypatch.setattr(
        target,
        "get_settings_refactor_phase_sequence",
        lambda: phases,
    )

    foundation_context = {
        "stats": {
            "system_total": "3",
            "module_total": 2,
            "history_total": "4",
        },
        "missing_tables": [],
        "recent_change_logs": [
            {
                "id": 1,
            },
        ],
    }

    profile_context = {
        "profile": "admin",
    }

    foundation_before = copy.deepcopy(
        foundation_context
    )

    profile_before = copy.deepcopy(
        profile_context
    )

    report = (
        target.build_settings_final_hardening_report(
            foundation_context=foundation_context,
            profile_context=profile_context,
        )
    )

    assert foundation_context == foundation_before
    assert profile_context == profile_before

    assert report["ok"] is True
    assert (
        report["phase"]
        == "settings_faz12_final_hardening"
    )

    assert report["summary"] == {
        "completed_phase_count": 9,
        "phase_total": 9,
        "module_total": 2,
        "unavailable_module_total": 0,
        "missing_table_total": 0,
        "system_setting_total": 3,
        "module_setting_total": 2,
        "history_total": 4,
    }

    assert report["phase_sequence"] is phases
    assert report["quality_snapshot"] is snapshot

    assert [
        item["code"]
        for item in report["guard_results"]
    ] == [
        "phase_sequence.closed",
        "service_modules.available",
        "foundation_tables.ready",
        "history_context.readable",
        "settings_counts.visible",
        "write_side_effects.none",
    ]

    assert all(
        item["ok"]
        for item in report["guard_results"]
    )

    assert report["release_checklist"] == [
        dict(item)
        for item in target.FINAL_HARDENING_GUARDS
    ]

    assert report["required_tables"] == list(
        target.FINAL_SETTINGS_TABLES
    )

    assert report["required_modules"] == list(
        target.FINAL_REQUIRED_SERVICE_MODULES
    )


def test_build_report_exposes_failed_guards(
    monkeypatch,
) -> None:
    snapshot = {
        "ok": False,
        "module_states": [
            {
                "name": "missing_module",
                "available": False,
            },
        ],
    }

    phases = [
        {
            "phase": 4,
            "status": "aktif",
        },
        {
            "phase": 5,
            "status": "s\u0131rada",
        },
    ]

    monkeypatch.setattr(
        target,
        "build_settings_refactor_quality_snapshot",
        lambda: snapshot,
    )

    monkeypatch.setattr(
        target,
        "get_settings_refactor_phase_sequence",
        lambda: phases,
    )

    report = (
        target.build_settings_final_hardening_report(
            foundation_context={
                "stats": {
                    "system_total": -1,
                    "module_total": "-2",
                    "history_total": "bad",
                },
                "missing_tables": [
                    "system_settings",
                ],
            },
            profile_context={},
        )
    )

    assert report["ok"] is False

    failing_codes = {
        item["code"]
        for item in report["guard_results"]
        if not item["ok"]
    }

    assert failing_codes == {
        "phase_sequence.closed",
        "service_modules.available",
        "foundation_tables.ready",
        "history_context.readable",
        "settings_counts.visible",
    }

    assert report["summary"] == {
        "completed_phase_count": 0,
        "phase_total": 2,
        "module_total": 1,
        "unavailable_module_total": 1,
        "missing_table_total": 1,
        "system_setting_total": -1,
        "module_setting_total": -2,
        "history_total": 0,
    }


def test_assert_contract_returns_success_and_forwards_context(
    monkeypatch,
) -> None:
    foundation = {
        "foundation": True,
    }

    profile = {
        "profile": True,
    }

    expected_report = {
        "ok": True,
        "guard_results": [],
    }

    calls: list[
        tuple[
            dict[str, object] | None,
            dict[str, object] | None,
        ]
    ] = []

    def fake_build(
        *,
        foundation_context=None,
        profile_context=None,
    ):
        calls.append(
            (
                foundation_context,
                profile_context,
            )
        )

        return expected_report

    monkeypatch.setattr(
        target,
        "build_settings_final_hardening_report",
        fake_build,
    )

    result = (
        target.assert_settings_final_hardening_contract(
            foundation_context=foundation,
            profile_context=profile,
        )
    )

    assert result is expected_report

    assert calls == [
        (
            foundation,
            profile,
        ),
    ]


def test_assert_contract_raises_codes_and_unknown(
    monkeypatch,
) -> None:
    def failing_report(
        *,
        foundation_context=None,
        profile_context=None,
    ):
        return {
            "ok": False,
            "guard_results": [
                {
                    "code": "alpha",
                    "ok": False,
                },
                {
                    "code": "beta",
                    "ok": False,
                },
                {
                    "code": "ignored",
                    "ok": True,
                },
            ],
        }

    monkeypatch.setattr(
        target,
        "build_settings_final_hardening_report",
        failing_report,
    )

    with pytest.raises(
        ValueError,
        match="alpha, beta",
    ):
        target.assert_settings_final_hardening_contract()

    def empty_failure(
        *,
        foundation_context=None,
        profile_context=None,
    ):
        return {
            "ok": False,
            "guard_results": [],
        }

    monkeypatch.setattr(
        target,
        "build_settings_final_hardening_report",
        empty_failure,
    )

    with pytest.raises(
        ValueError,
        match="unknown",
    ):
        target.assert_settings_final_hardening_contract()
