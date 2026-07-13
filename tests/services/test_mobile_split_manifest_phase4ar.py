from __future__ import annotations

from app.api.mobile.services import split_manifest as svc


def test_mobile_route_split_manifest_public_contract() -> None:
    assert svc.__name__ == "app.api.mobile.services.split_manifest"
    assert "Planned BYS360 mobile route split manifest" in (svc.__doc__ or "")

    manifest = svc.MOBILE_ROUTE_SPLIT_MANIFEST

    assert set(manifest) == {
        "app/api/mobile/routes.py",
        "app/api/mobile/performance_routes.py",
    }


def test_mobile_routes_manifest_target_groups_are_preserved() -> None:
    manifest = svc.MOBILE_ROUTE_SPLIT_MANIFEST
    route_manifest = manifest["app/api/mobile/routes.py"]

    assert route_manifest["rule"] == (
        "Do not change URL paths, endpoint names or blueprint registration during extraction."
    )

    assert route_manifest["target_groups"] == {
        "auth": "app/api/mobile/services/auth_service.py",
        "dashboard": "app/api/mobile/services/dashboard_service.py",
        "profile": "app/api/mobile/services/profile_service.py",
        "personnel": "app/api/mobile/services/personnel_service.py",
        "communication": "app/api/mobile/services/communication_service.py",
        "survey": "app/api/mobile/services/survey_service.py",
        "support": "app/api/mobile/services/support_service.py",
        "assistant": "app/api/mobile/services/assistant_service.py",
    }


def test_mobile_performance_routes_manifest_target_groups_are_preserved() -> None:
    manifest = svc.MOBILE_ROUTE_SPLIT_MANIFEST
    performance_manifest = manifest["app/api/mobile/performance_routes.py"]

    assert performance_manifest["rule"] == (
        "Move one function group per package and run compileall + create_app after every micro step."
    )

    assert performance_manifest["target_groups"] == {
        "performance_periods": "app/api/mobile/services/performance_period_service.py",
        "performance_tasks": "app/api/mobile/services/performance_task_service.py",
        "performance_evaluation": "app/api/mobile/services/performance_evaluation_service.py",
        "performance_summary": "app/api/mobile/services/performance_summary_service.py",
        "performance_scorecard": "app/api/mobile/services/performance_scorecard_service.py",
    }
