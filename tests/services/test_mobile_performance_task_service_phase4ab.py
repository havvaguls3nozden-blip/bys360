from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any
import sys

import pytest

PHASE4AB_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PHASE4AB_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE4AB_PROJECT_ROOT))

from app.api.mobile.services import performance_task_service as svc


def _install_fake_performance_routes(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, tuple[Any, ...], dict[str, Any]]]:
    calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
    fake_routes = ModuleType("app.api.mobile.performance_routes")

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

    fake_routes._bys360_legacy__v2835_score_form_payload = make_legacy("score_form_payload")
    fake_routes._bys360_legacy__v2837_action_capabilities = make_legacy("action_capabilities")
    fake_routes._bys360_legacy__v2837_find_return_target = make_legacy("find_return_target")
    fake_routes._bys360_legacy__v2837_return_assignment = make_legacy("return_assignment")
    fake_routes._bys360_legacy__v2837_withdraw_assignment = make_legacy("withdraw_assignment")

    monkeypatch.setitem(sys.modules, "app.api.mobile.performance_routes", fake_routes)

    import app.api.mobile as mobile_pkg

    monkeypatch.setattr(mobile_pkg, "performance_routes", fake_routes, raising=False)
    return calls


def test_phase4ab_success_delegates_forward_args_and_kwargs(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_fake_performance_routes(monkeypatch)

    assert svc.delegate_v2835_score_form_payload(1, mode="preview") == {
        "ok": True,
        "delegate": "score_form_payload",
        "args": [1],
        "kwargs": {"mode": "preview"},
    }

    assert svc._v2837_action_capabilities(2, user="u1")["delegate"] == "action_capabilities"
    assert svc._v2837_find_return_target(3, task_id=7)["delegate"] == "find_return_target"
    assert svc._v2837_return_assignment(4, reason="return")["delegate"] == "return_assignment"
    assert svc._v2837_withdraw_assignment(5, reason="withdraw")["delegate"] == "withdraw_assignment"

    assert [item[0] for item in calls] == [
        "score_form_payload",
        "action_capabilities",
        "find_return_target",
        "return_assignment",
        "withdraw_assignment",
    ]


def test_phase4ab_delegate_v2835_missing_legacy_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_routes = ModuleType("app.api.mobile.performance_routes")
    monkeypatch.setitem(sys.modules, "app.api.mobile.performance_routes", fake_routes)

    import app.api.mobile as mobile_pkg

    monkeypatch.setattr(mobile_pkg, "performance_routes", fake_routes, raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        svc.delegate_v2835_score_form_payload()

    assert "_bys360_legacy__v2835_score_form_payload" in str(exc_info.value)


def test_phase4ab_public_contract_is_stable() -> None:
    assert callable(svc.delegate_v2835_score_form_payload)
    assert callable(svc._v2837_action_capabilities)
    assert callable(svc._v2837_find_return_target)
    assert callable(svc._v2837_return_assignment)
    assert callable(svc._v2837_withdraw_assignment)
