# BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7
"""Planned BYS360 mobile route split manifest."""
from __future__ import annotations


MOBILE_ROUTE_SPLIT_MANIFEST: dict[str, dict[str, object]] = {
    "app/api/mobile/routes.py": {
        "target_groups": {
            "auth": "app/api/mobile/services/auth_service.py",
            "dashboard": "app/api/mobile/services/dashboard_service.py",
            "profile": "app/api/mobile/services/profile_service.py",
            "personnel": "app/api/mobile/services/personnel_service.py",
            "communication": "app/api/mobile/services/communication_service.py",
            "survey": "app/api/mobile/services/survey_service.py",
            "support": "app/api/mobile/services/support_service.py",
            "assistant": "app/api/mobile/services/assistant_service.py",
        },
        "rule": "Do not change URL paths, endpoint names or blueprint registration during extraction.",
    },
    "app/api/mobile/performance_routes.py": {
        "target_groups": {
            "performance_periods": "app/api/mobile/services/performance_period_service.py",
            "performance_tasks": "app/api/mobile/services/performance_task_service.py",
            "performance_evaluation": "app/api/mobile/services/performance_evaluation_service.py",
            "performance_summary": "app/api/mobile/services/performance_summary_service.py",
            "performance_scorecard": "app/api/mobile/services/performance_scorecard_service.py",
        },
        "rule": "Move one function group per package and run compileall + create_app after every micro step.",
    },
}
