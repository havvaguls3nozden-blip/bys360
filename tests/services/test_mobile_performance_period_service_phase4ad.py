from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

PHASE4AD_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PHASE4AD_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE4AD_PROJECT_ROOT))


def _install_fake_performance_routes(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, tuple[Any, ...], dict[str, Any]]]:
    calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
    # This stand-in has no fixed attribute contract -- its entire purpose is
    # to receive whatever ad hoc legacy delegate symbols are attached below,
    # exactly like a real module's namespace after exec. `Any` is the
    # accurate type here, not a loosened one (same pattern already
    # established for the STUB_MODULES construction in
    # tests/services/test_settings_campaign2_wave2_phase4du.py).
    fake_routes: Any = ModuleType("app.api.mobile.performance_routes")

    def make_legacy(name: str):
        def legacy(*args: Any, **kwargs: Any) -> dict[str, Any]:
            calls.append((name, args, kwargs))
            return {
                "ok": True,
                "delegate": name,
                "args": list(args),
                "kwargs": kwargs,
            }

        return legacy

    fake_routes._bys360_legacy__v2853_note_type_label = make_legacy("note_type_label")
    fake_routes._bys360_legacy__v2853_note_bool = make_legacy("note_bool")
    fake_routes._bys360_legacy_mobile_performance_in_period_notes = make_legacy("in_period_notes")
    fake_routes._bys360_legacy_mobile_performance_in_period_notes_v2853 = make_legacy("in_period_notes_v2853")
    fake_routes._bys360_legacy_mobile_performance_note_scorecard_v2863a = make_legacy("note_scorecard_v2863a")
    fake_routes._bys360_legacy_mobile_performance_period_detail = make_legacy("period_detail")
    fake_routes._bys360_legacy__period_scope = make_legacy("period_scope")
    fake_routes._bys360_legacy__period_progress = make_legacy("period_progress")

    monkeypatch.setitem(sys.modules, "app.api.mobile.performance_routes", fake_routes)

    import app.api.mobile as mobile_pkg

    monkeypatch.setattr(mobile_pkg, "performance_routes", fake_routes, raising=False)
    return calls


def test_phase4ad_period_service_delegates_forward_args_and_kwargs(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.api.mobile.services import performance_period_service as svc

    calls = _install_fake_performance_routes(monkeypatch)

    assert svc._v2853_note_type_label(1, label="ara") == {
        "ok": True,
        "delegate": "note_type_label",
        "args": [1],
        "kwargs": {"label": "ara"},
    }

    assert svc._v2853_note_bool(2, enabled=True)["delegate"] == "note_bool"
    assert svc.delegate_mobile_performance_in_period_notes(3, period_id=10)["delegate"] == "in_period_notes"
    assert svc.delegate_mobile_performance_in_period_notes_v2853(4, period_id=11)["delegate"] == "in_period_notes_v2853"
    assert svc.delegate_mobile_performance_note_scorecard_v2863a(5, scorecard_id=12)["delegate"] == "note_scorecard_v2863a"
    assert svc.mobile_performance_period_detail(6, detail=True)["delegate"] == "period_detail"
    assert svc._period_scope(7, scope="unit")["delegate"] == "period_scope"
    assert svc._period_progress(8, progress="open")["delegate"] == "period_progress"

    assert [item[0] for item in calls] == [
        "note_type_label",
        "note_bool",
        "in_period_notes",
        "in_period_notes_v2853",
        "note_scorecard_v2863a",
        "period_detail",
        "period_scope",
        "period_progress",
    ]


def test_phase4ad_public_contract_is_stable() -> None:
    from app.api.mobile.services import performance_period_service as svc

    assert callable(svc._v2853_note_type_label)
    assert callable(svc._v2853_note_bool)
    assert callable(svc.delegate_mobile_performance_in_period_notes)
    assert callable(svc.delegate_mobile_performance_in_period_notes_v2853)
    assert callable(svc.delegate_mobile_performance_note_scorecard_v2863a)
    assert callable(svc.mobile_performance_period_detail)
    assert callable(svc._period_scope)
    assert callable(svc._period_progress)
