from __future__ import annotations

import sys
import types
from typing import Any

import pytest

import app.api.mobile as mobile_package
from app.api.mobile.services import communication_service as svc


DELEGATES = [
    (
        "mobile_b48_communication_v2_create_thread_delegate",
        "_bys360_legacy_mobile_b48_communication_v2_create_thread",
    ),
    (
        "mobile_b48_communication_v2_users_delegate",
        "_bys360_legacy_mobile_b48_communication_v2_users",
    ),
    (
        "mobile_b48_communication_v2_send_delegate",
        "_bys360_legacy_mobile_b48_communication_v2_send",
    ),
    (
        "mobile_b48_communication_v2_thread_detail_delegate",
        "_bys360_legacy_mobile_b48_communication_v2_thread_detail",
    ),
    (
        "_b48_thread_row_delegate",
        "_bys360_legacy__b48_thread_row",
    ),
    (
        "mobile_b46_communication_create_thread_delegate",
        "_bys360_legacy_mobile_b46_communication_create_thread",
    ),
    (
        "mobile_b46_communication_send_message_delegate",
        "_bys360_legacy_mobile_b46_communication_send_message",
    ),
    (
        "mobile_b46_communication_thread_detail_delegate",
        "_bys360_legacy_mobile_b46_communication_thread_detail",
    ),
    (
        "_b46_thread_row_delegate",
        "_bys360_legacy__b46_thread_row",
    ),
]


def _install_fake_mobile_routes(monkeypatch: pytest.MonkeyPatch, **handlers: Any) -> types.ModuleType:
    fake_routes = types.ModuleType("app.api.mobile.routes")

    for name, handler in handlers.items():
        setattr(fake_routes, name, handler)

    monkeypatch.setitem(sys.modules, "app.api.mobile.routes", fake_routes)
    monkeypatch.setattr(mobile_package, "routes", fake_routes, raising=False)
    return fake_routes


@pytest.mark.parametrize(("delegate_name", "legacy_name"), DELEGATES)
def test_mobile_communication_delegate_calls_legacy_handler(
    monkeypatch: pytest.MonkeyPatch,
    delegate_name: str,
    legacy_name: str,
) -> None:
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def legacy_handler(*args: Any, **kwargs: Any) -> dict[str, Any]:
        calls.append((args, kwargs))
        return {
            "handler": legacy_name,
            "args": args,
            "kwargs": kwargs,
        }

    _install_fake_mobile_routes(monkeypatch, **{legacy_name: legacy_handler})

    delegate = getattr(svc, delegate_name)
    result = delegate("alpha", 42, mode="mobile")

    assert result == {
        "handler": legacy_name,
        "args": ("alpha", 42),
        "kwargs": {"mode": "mobile"},
    }
    assert calls == [(("alpha", 42), {"mode": "mobile"})]


@pytest.mark.parametrize(("delegate_name", "legacy_name"), DELEGATES)
def test_mobile_communication_delegate_raises_when_legacy_handler_missing(
    monkeypatch: pytest.MonkeyPatch,
    delegate_name: str,
    legacy_name: str,
) -> None:
    _install_fake_mobile_routes(monkeypatch)

    delegate = getattr(svc, delegate_name)

    with pytest.raises(RuntimeError) as exc_info:
        delegate("alpha", mode="mobile")

    message = str(exc_info.value)
    assert "BYS360 communication legacy handler not found" in message
    assert legacy_name in message
