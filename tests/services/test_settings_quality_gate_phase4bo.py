from __future__ import annotations

from types import SimpleNamespace

import app.services.settings.quality_gate as quality_gate


def test_phase_sequence_is_ordered_serialized_and_detached() -> None:
    sequence = quality_gate.get_settings_refactor_phase_sequence()

    assert len(sequence) == len(
        quality_gate.SETTINGS_REFACTOR_PHASES
    )
    assert sequence[0]["phase"] == "Faz 4"
    assert sequence[-1]["phase"] == "Faz 12"
    assert sequence[0]["module"] == (
        "app.services.settings.change_logs"
    )
    assert sequence[-1]["module"] == (
        "app.services.settings.final_hardening"
    )
    assert sequence[0]["status"] == (
        quality_gate.SETTINGS_REFACTOR_PHASES[0].status
    )

    sequence[0]["phase"] = "changed"

    assert quality_gate.SETTINGS_REFACTOR_PHASES[0].phase == (
        "Faz 4"
    )


def test_module_symbol_state_reports_available_and_missing(
    monkeypatch,
) -> None:
    module = SimpleNamespace(alpha=object())

    def fake_import(module_name: str):
        assert module_name == "module.sample"
        return module

    monkeypatch.setattr(
        quality_gate,
        "import_module",
        fake_import,
    )

    available = quality_gate._module_symbol_state(
        "module.sample",
        ("alpha",),
    )
    missing = quality_gate._module_symbol_state(
        "module.sample",
        ("alpha", "beta"),
    )

    assert available == {
        "module": "module.sample",
        "available": True,
        "missing_symbols": [],
        "error": "",
    }

    assert missing == {
        "module": "module.sample",
        "available": False,
        "missing_symbols": ["beta"],
        "error": "",
    }


def test_module_symbol_state_handles_import_failure(
    monkeypatch,
) -> None:
    def failing_import(module_name: str):
        raise RuntimeError(
            f"cannot import {module_name}"
        )

    monkeypatch.setattr(
        quality_gate,
        "import_module",
        failing_import,
    )

    state = quality_gate._module_symbol_state(
        "module.failed",
        ("alpha", "beta"),
    )

    assert state == {
        "module": "module.failed",
        "available": False,
        "missing_symbols": ["alpha", "beta"],
        "error": "cannot import module.failed",
    }


def test_quality_snapshot_reports_missing_and_pending_items(
    monkeypatch,
) -> None:
    completed_status = (
        quality_gate.SETTINGS_REFACTOR_PHASES[0].status
    )

    completed = quality_gate.SettingsRefactorPhase(
        phase="Faz X",
        title="Completed",
        status=completed_status,
        module="module.ok",
    )
    pending = quality_gate.SettingsRefactorPhase(
        phase="Faz Y",
        title="Pending",
        status="pending",
        module="module.bad",
    )

    monkeypatch.setattr(
        quality_gate,
        "SETTINGS_REFACTOR_PHASES",
        (completed, pending),
    )
    monkeypatch.setattr(
        quality_gate,
        "REQUIRED_SERVICE_SYMBOLS",
        {
            "module.ok": ("alpha",),
            "module.bad": ("beta",),
        },
    )

    states = {
        "module.ok": {
            "module": "module.ok",
            "available": True,
            "missing_symbols": [],
            "error": "",
        },
        "module.bad": {
            "module": "module.bad",
            "available": False,
            "missing_symbols": ["beta"],
            "error": "",
        },
    }

    def fake_state(
        module_name: str,
        symbols: tuple[str, ...],
    ):
        assert symbols
        return states[module_name]

    monkeypatch.setattr(
        quality_gate,
        "_module_symbol_state",
        fake_state,
    )

    snapshot = (
        quality_gate.build_settings_refactor_quality_snapshot()
    )

    assert snapshot["ok"] is False
    assert snapshot["phase"] == (
        "settings_faz12_final_quality_gate"
    )
    assert snapshot["completed_phase_count"] == 1
    assert snapshot["module_states"] == [
        states["module.ok"],
        states["module.bad"],
    ]
    assert snapshot["next_phases"] == [
        {
            "phase": "Faz Y",
            "title": "Pending",
            "status": "pending",
            "module": "module.bad",
        }
    ]


def test_quality_snapshot_reports_all_complete(
    monkeypatch,
) -> None:
    completed_status = (
        quality_gate.SETTINGS_REFACTOR_PHASES[0].status
    )

    phases = (
        quality_gate.SettingsRefactorPhase(
            phase="Faz A",
            title="First",
            status=completed_status,
            module="module.one",
        ),
        quality_gate.SettingsRefactorPhase(
            phase="Faz B",
            title="Second",
            status=completed_status,
            module="module.two",
        ),
    )

    monkeypatch.setattr(
        quality_gate,
        "SETTINGS_REFACTOR_PHASES",
        phases,
    )
    monkeypatch.setattr(
        quality_gate,
        "REQUIRED_SERVICE_SYMBOLS",
        {
            "module.one": ("alpha",),
            "module.two": ("beta",),
        },
    )

    def available_state(
        module_name: str,
        symbols: tuple[str, ...],
    ):
        return {
            "module": module_name,
            "available": True,
            "missing_symbols": [],
            "error": "",
        }

    monkeypatch.setattr(
        quality_gate,
        "_module_symbol_state",
        available_state,
    )

    snapshot = (
        quality_gate.build_settings_refactor_quality_snapshot()
    )

    assert snapshot["ok"] is True
    assert snapshot["completed_phase_count"] == 2
    assert snapshot["next_phases"] == []
    assert len(snapshot["module_states"]) == 2


def test_template_guard_context_handles_empty_and_populated_inputs(
    monkeypatch,
) -> None:
    snapshot = {
        "ok": True,
        "phase": "test",
    }

    monkeypatch.setattr(
        quality_gate,
        "build_settings_refactor_quality_snapshot",
        lambda: snapshot,
    )

    empty = quality_gate.build_settings_template_guard_context()

    assert empty == {
        "quality_snapshot": snapshot,
        "has_foundation_context": False,
        "has_profile_context": False,
        "foundation_db_ready": False,
        "history_total": 0,
    }

    populated = (
        quality_gate.build_settings_template_guard_context(
            foundation_context={
                "db_ready": 1,
                "stats": {
                    "history_total": "7",
                },
            },
            profile_context={
                "profile": True,
            },
        )
    )

    assert populated == {
        "quality_snapshot": snapshot,
        "has_foundation_context": True,
        "has_profile_context": True,
        "foundation_db_ready": True,
        "history_total": 7,
    }
