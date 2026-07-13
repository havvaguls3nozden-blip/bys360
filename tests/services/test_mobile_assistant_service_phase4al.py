from __future__ import annotations

import sys
import types
from typing import Any

import pytest

import app.api.mobile as mobile_pkg
from app.api.mobile.services import assistant_service as svc


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


def test_delegate_mobile_b49_assistant_v2_ask_forwards_to_legacy(
    fake_mobile_routes: types.ModuleType,
) -> None:
    legacy = _recording_legacy({"answer": "ok"})
    setattr(fake_mobile_routes, "_bys360_legacy_mobile_b49_assistant_v2_ask", legacy)

    result = svc.delegate_mobile_b49_assistant_v2_ask("hello", user_id=42)

    assert result == {"answer": "ok"}
    assert legacy.calls == [  # type: ignore[attr-defined]
        {"args": ("hello",), "kwargs": {"user_id": 42}}
    ]


def test_delegate_mobile_b49_assistant_v2_ask_raises_when_legacy_missing(
    fake_mobile_routes: types.ModuleType,
) -> None:
    with pytest.raises(AttributeError, match="_bys360_legacy_mobile_b49_assistant_v2_ask"):
        svc.delegate_mobile_b49_assistant_v2_ask()
