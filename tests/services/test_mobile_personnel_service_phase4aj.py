from __future__ import annotations

import sys
import types
from typing import Any

import pytest

import app.api.mobile as mobile_pkg
import app.api.mobile.domains as domains_pkg
from app.api.mobile.services import personnel_service as svc


@pytest.fixture()
def fake_mobile_routes(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    fake = types.ModuleType("app.api.mobile.routes")
    monkeypatch.setitem(sys.modules, "app.api.mobile.routes", fake)
    monkeypatch.setattr(mobile_pkg, "routes", fake, raising=False)
    return fake


@pytest.fixture()
def fake_personnel_domain(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    fake = types.ModuleType("app.api.mobile.domains.personnel_write_all")
    monkeypatch.setitem(sys.modules, "app.api.mobile.domains.personnel_write_all", fake)
    monkeypatch.setattr(domains_pkg, "personnel_write_all", fake, raising=False)
    return fake


def _recording_legacy(return_value: Any):
    calls: list[dict[str, Any]] = []

    def legacy(*args: Any, **kwargs: Any) -> Any:
        calls.append({"args": args, "kwargs": kwargs})
        return return_value

    legacy.calls = calls  # type: ignore[attr-defined]
    return legacy


def test_routes_module_returns_mobile_routes(fake_mobile_routes: types.ModuleType) -> None:
    assert svc._routes_module() is fake_mobile_routes


def test_personnel_domain_module_returns_domain(
    fake_personnel_domain: types.ModuleType,
) -> None:
    assert svc._personnel_domain_module() is fake_personnel_domain


def test_mobile_personnel_all_delegates_to_routes(
    fake_mobile_routes: types.ModuleType,
) -> None:
    legacy = _recording_legacy({"items": ["person-1"]})
    # fake_mobile_routes is a ModuleType stand-in with no fixed attribute
    # contract -- its entire purpose is to receive this ad hoc legacy
    # delegate symbol, exactly like a real module's namespace after exec.
    routes: Any = fake_mobile_routes
    routes._bys360_legacy_mobile_personnel_all = legacy

    result = svc.mobile_personnel_all("filter-1", page=2)

    assert result == {"items": ["person-1"]}
    assert legacy.calls == [
        {"args": ("filter-1",), "kwargs": {"page": 2}}
    ]


def test_mobile_personnel_create_delegates_to_personnel_domain(
    fake_personnel_domain: types.ModuleType,
) -> None:
    legacy = _recording_legacy({"created": True})
    # Same rationale as fake_mobile_routes above.
    domain: Any = fake_personnel_domain
    domain._bys360_legacy_mobile_personnel_create = legacy

    result = svc.mobile_personnel_create({"name": "Ada"}, source="mobile")

    assert result == {"created": True}
    assert legacy.calls == [
        {"args": ({"name": "Ada"},), "kwargs": {"source": "mobile"}}
    ]


def test_mobile_created_personnel_row_delegates_to_personnel_domain(
    fake_personnel_domain: types.ModuleType,
) -> None:
    legacy = _recording_legacy({"row": {"id": 7}})
    # Same rationale as fake_mobile_routes above.
    domain: Any = fake_personnel_domain
    domain._bys360_legacy__mobile_created_personnel_row = legacy

    result = svc._mobile_created_personnel_row(7, include_meta=True)

    assert result == {"row": {"id": 7}}
    assert legacy.calls == [
        {"args": (7,), "kwargs": {"include_meta": True}}
    ]
