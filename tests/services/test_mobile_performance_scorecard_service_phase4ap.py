from __future__ import annotations

from app.api.mobile.services import performance_scorecard_service as svc


def test_performance_scorecard_service_scaffold_import_contract() -> None:
    assert svc.__name__ == "app.api.mobile.services.performance_scorecard_service"
    assert "Performance scorecard service extraction target" in (svc.__doc__ or "")
    assert [name for name in dir(svc) if not name.startswith("__")] == ["annotations"]
