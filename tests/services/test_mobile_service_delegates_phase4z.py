from __future__ import annotations

import sys
from pathlib import Path

PHASE4Z_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PHASE4Z_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE4Z_PROJECT_ROOT))

from app.api.mobile.services import base
from app.api.mobile.services import dashboard_service as dashboard
from app.api.mobile.services import profile_service as profile


def test_phase4z_base_payload_helpers_are_stable() -> None:
    data = {"user": "BYS360", "count": 2}

    ok = base.ok_payload(data)
    assert isinstance(ok, dict)
    assert ok.get("ok") is True
    assert ok.get("user") == "BYS360"
    assert ok.get("count") == 2

    err = base.error_payload("Hata mesajı")
    assert isinstance(err, dict)
    assert err.get("ok") is False
    assert "Hata mesajı" in str(err)


def test_phase4z_profile_legacy_delegates_return_legacy_result() -> None:
    calls: list[str] = []

    def legacy_profile():
        calls.append("profile")
        return {"profile": True}

    def legacy_update():
        calls.append("update")
        return {"updated": True}

    def legacy_me():
        calls.append("me")
        return {"me": True}

    assert profile.delegate_mobile_profile(legacy_profile) == {"profile": True}
    assert profile.delegate_mobile_profile_update(legacy_update) == {"updated": True}
    assert profile.delegate_mobile_profile_me(legacy_me) == {"me": True}
    assert calls == ["profile", "update", "me"]


def test_phase4z_dashboard_legacy_delegates_return_legacy_result() -> None:
    calls: list[str] = []

    def make_legacy(name: str):
        def legacy():
            calls.append(name)
            return {"delegate": name}
        return legacy

    assert dashboard.delegate_mobile_dashboard_summary(make_legacy("summary")) == {"delegate": "summary"}
    assert dashboard.delegate_mobile_kpi_target_management_v2853(make_legacy("management")) == {"delegate": "management"}
    assert dashboard.delegate_mobile_kpi_target_create_v2853(make_legacy("create")) == {"delegate": "create"}
    assert dashboard.delegate_mobile_kpi_target_progress_v2853(make_legacy("progress")) == {"delegate": "progress"}

    assert dashboard.mobile_dashboard_summary_delegate(make_legacy("summary2")) == {"delegate": "summary2"}
    assert dashboard.mobile_kpi_target_management_v2853_delegate(make_legacy("management2")) == {"delegate": "management2"}
    assert dashboard.mobile_kpi_target_create_v2853_delegate(make_legacy("create2")) == {"delegate": "create2"}
    assert dashboard.mobile_kpi_target_progress_v2853_delegate(make_legacy("progress2")) == {"delegate": "progress2"}

    assert calls == [
        "summary",
        "management",
        "create",
        "progress",
        "summary2",
        "management2",
        "create2",
        "progress2",
    ]
