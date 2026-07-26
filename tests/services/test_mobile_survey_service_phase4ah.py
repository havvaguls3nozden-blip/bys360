from __future__ import annotations

import sys
import types
from typing import Any

import pytest

import app.api.mobile as mobile_pkg
from app.api.mobile.services import survey_service as svc


@pytest.fixture()
def fake_mobile_routes(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    fake = types.ModuleType("app.api.mobile.routes")
    monkeypatch.setitem(sys.modules, "app.api.mobile.routes", fake)
    monkeypatch.setattr(mobile_pkg, "routes", fake, raising=False)
    return fake


def _recording_legacy(return_value: Any):
    calls: list[dict[str, Any]] = []

    def legacy(*args: Any, **kwargs: Any) -> Any:
        calls.append({"args": args, "kwargs": kwargs})
        return return_value

    legacy.calls = calls  # type: ignore[attr-defined]
    return legacy


def test_call_legacy_invokes_named_handler(fake_mobile_routes: types.ModuleType) -> None:
    legacy = _recording_legacy({"ok": True})
    fake_mobile_routes._bys360_legacy_mobile_survey_custom = legacy

    result = svc._call_legacy("mobile_survey_custom", "person-1", page=2)

    assert result == {"ok": True}
    assert legacy.calls == [  # type: ignore[attr-defined]
        {"args": ("person-1",), "kwargs": {"page": 2}}
    ]


def test_call_legacy_missing_handler_raises(fake_mobile_routes: types.ModuleType) -> None:
    with pytest.raises(RuntimeError, match="mobile_survey_missing"):
        svc._call_legacy("mobile_survey_missing")


@pytest.mark.parametrize(
    ("function_name", "legacy_attr", "marker"),
    [
        (
            "_mobile_survey_detail_payload",
            "_bys360_legacy__mobile_survey_detail_payload",
            "detail",
        ),
        (
            "_mobile_survey_validate_answers",
            "_bys360_legacy__mobile_survey_validate_answers",
            "validate",
        ),
        (
            "mobile_survey_submit",
            "_bys360_legacy_mobile_survey_submit",
            "submit",
        ),
    ],
)
def test_survey_delegate_wrappers_forward_to_expected_legacy(
    fake_mobile_routes: types.ModuleType,
    function_name: str,
    legacy_attr: str,
    marker: str,
) -> None:
    legacy = _recording_legacy({"marker": marker})
    setattr(fake_mobile_routes, legacy_attr, legacy)

    delegate = getattr(svc, function_name)
    result = delegate("survey-1", answers={"q1": "yes"})

    assert result == {"marker": marker}
    assert legacy.calls == [  # type: ignore[attr-defined]
        {"args": ("survey-1",), "kwargs": {"answers": {"q1": "yes"}}}
    ]


@pytest.mark.parametrize(
    ("function_name", "missing_name"),
    [
        ("_mobile_survey_detail_payload", "_mobile_survey_detail_payload"),
        ("_mobile_survey_validate_answers", "_mobile_survey_validate_answers"),
        ("mobile_survey_submit", "mobile_survey_submit"),
    ],
)
def test_survey_delegate_wrappers_raise_when_legacy_missing(
    fake_mobile_routes: types.ModuleType,
    function_name: str,
    missing_name: str,
) -> None:
    delegate = getattr(svc, function_name)

    with pytest.raises(RuntimeError, match=missing_name):
        delegate()
