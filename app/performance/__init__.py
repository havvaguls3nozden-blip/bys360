"""Performans paket kaydı ve modüler route yükleme noktası.

Bu dosya performans alanındaki route ailelerini tek merkezden yükler.
Opsiyonel faz route'ları sessizce yutulmaz; yükleme hataları loglanır.
Böylece canlıda route eksikliği 404 olarak gizlenmeden loglardan izlenebilir.
"""
from __future__ import annotations

import importlib
import logging

from flask import Blueprint

performance_bp = Blueprint("performance", __name__, url_prefix="/performans")

logger = logging.getLogger(__name__)


def _optional_import(module_name: str) -> None:
    """Opsiyonel performans route modülünü güvenli ve loglu yükler."""
    try:
        importlib.import_module(f"{__name__}.{module_name}")
    except Exception as exc:  # pragma: no cover - canlı log güvenliği
        logger.exception("BYS360 performans route modülü yüklenemedi: %s | %s", module_name, exc)


# Çekirdek route aileleri uygulama açılışında görünür hata versin.
from . import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    admin_core_routes,  # noqa: E402,F401
    assignment_rule_routes,  # noqa: E402,F401
    core_health_routes,  # noqa: E402,F401
    engagement_routes,  # noqa: E402,F401
    evaluation_core_routes,  # noqa: E402,F401
    hierarchy_ui_routes,  # noqa: E402,F401
    history_import_routes,  # noqa: E402,F401
    low_score_process_routes,  # noqa: E402,F401
    ops_routes,  # noqa: E402,F401
    president_approval_card_routes as _president_approval_card_routes,  # noqa: E402,F401  # BYS360_PRESIDENT_APPROVAL_CARD_ROUTE_IMPORT
    process_engine_phase6_president_approvals_routes,  # noqa: E402,F401
    reporting_routes,  # noqa: E402,F401
    routes,  # noqa: E402,F401
    task_routes,  # noqa: E402,F401
    v2_routes,  # noqa: E402,F401
)

OPTIONAL_ROUTE_MODULES = [
    # BYS360_PERFORMANCE_V2_1_22B_LIVE_TRACKING_ROUTE_IMPORT
    "v2_1_10_evaluation_live_tracking_routes",
    # BYS360_PERFORMANCE_V2_1_11_EVALUATOR_REMINDER_CENTER_ROUTE_IMPORT
    "v2_1_11_evaluator_reminder_center_routes",
    # BYS360_PERFORMANCE_V2_1_7_PERIOD_MANAGEMENT_CENTER_ROUTE_IMPORT
    "v2_1_7_period_management_center_routes",
    # BYS360_PERFORMANCE_V2_1_6_CATEGORY_PERIOD_INTEGRATION_ROUTE_IMPORT
    "v2_1_6_category_period_integration_routes",
    # BYS360_PERFORMANCE_V2_1_5_CATEGORY_PERIOD_SCOPE_ROUTE_IMPORT
    "v2_1_5_category_period_scope_routes",
    # BYS360_PERFORMANCE_V2_1_4_CATEGORY_SCOPE_ROUTE_IMPORT
    "v2_1_4_category_scope_routes",
    # BYS360_PERFORMANCE_V2_1_3_PERSONNEL_CATEGORY_CARD_ROUTE_IMPORT
    "v2_1_3_personnel_category_card_routes",
    # BYS360_PERFORMANCE_V2_1_2_PERSONNEL_CATEGORY_ROUTE_IMPORT
    "v2_1_2_category_routes",
    # BYS360_PERFORMANCE_V2_1_1_RULE_SETTINGS_ROUTE_IMPORT
    "v2_1_1_rule_settings_routes",
    # Faz 8 - Performans Süreç Takibi route yüklemesi
    "process_engine_phase8_tracking_routes",
    # Compatibility guard.
    "meeting_development_routes",
    # BYS360_MEETING_DEVELOPMENT_FAZ2_TEST_ROUTES_IMPORT
    "meeting_test_routes",
    # BYS360_MEETING_DEVELOPMENT_FAZ3_ROUTES_IMPORT
    "meeting_development_faz3_routes",
    # BYS360_MEETING_DEVELOPMENT_FAZ4_FINAL_GATE_ROUTES_IMPORT
    "meeting_development_faz4_routes",
    # BYS360_MEETING_RULE_ENFORCEMENT_ROUTES_IMPORT
    "meeting_rule_enforcement_routes",
    # BYS360_MEETING_P0_COMPLETION_ROUTES_IMPORT
    "meeting_p0_completion_routes",
    # BYS360_MEETING_P1_SCOPE_ROUTES_IMPORT
    "meeting_p1_scope_routes",
    # BYS360_MEETING_P2_ARCHIVE_NOTES_ROUTES_IMPORT
    "meeting_p2_archive_notes_routes",
    # BYS360_MEETING_P3_REMINDERS_ROUTES_IMPORT
    "meeting_p3_reminders_routes",
    # BYS360_MEETING_P4_DEVELOPMENT_GUIDANCE_ROUTES_IMPORT
    "meeting_p4_development_guidance_routes",
    # BYS360_MEETING_FINAL_CLOSURE_ROUTES_IMPORT
    "meeting_final_closure_routes",
    # BYS360_INTERIM_NOTES_MANAGER_INDEPENDENT_ROUTES_IMPORT
    # BYS360_INTERIM_NOTES_MENU_REDESIGN_V3_IMPORT
    "interim_notes_manager_routes",
    # BYS360_PHASE1_4B_PERSONNEL_SUPPORT_PUBLISH_APPROVAL_ROUTES_IMPORT
    "personnel_support_publish_approval_routes",
    # BYS360_PHASE7_2_PERFORMANCE_ARCHIVE_ROUTES_IMPORT
    # BYS360_PHASE7_3_PERFORMANCE_ARCHIVE_ROUTES_IMPORT
    # BYS360_PHASE7_4_PERFORMANCE_ARCHIVE_PERSONNEL_VISIBILITY_ROUTES_IMPORT
    # BYS360_PHASE7_5_PERFORMANCE_ARCHIVE_MANAGER_VISIBILITY_ROUTES_IMPORT
    "performance_archive_routes",
    # BYS360_FEEDBACK_AFTERCARE_PHASE1_ROUTES_IMPORT
    "feedback_aftercare_routes",
    # BYS360_FEEDBACK_GUIDE_PHASE2_ROUTES_IMPORT
    "feedback_meeting_guide_routes",
    # BYS360_FEEDBACK_INTEGRATION_PHASE3_ROUTES_IMPORT
    "feedback_integration_routes",
    # BYS360_FEEDBACK_FOLLOWUP_PHASE4_ROUTES_IMPORT
    "feedback_followup_phase4_routes",
    # BYS360_FEEDBACK_FINAL_GATE_PHASE5_ROUTES_IMPORT
    "feedback_final_gate_phase5_routes",
    # BYS360_FEEDBACK_CORPORATE_CLEANUP_PHASE6_ROUTES_IMPORT
    "feedback_corporate_cleanup_phase6_routes",
    # BYS360_FEEDBACK_PIPELINE_ROUTES_IMPORT
    "feedback_pipeline_routes",
]

for _module_name in OPTIONAL_ROUTE_MODULES:
    _optional_import(_module_name)

# /BYS360_PHASE7_2_PERFORMANCE_ARCHIVE_ROUTES_IMPORT
# /BYS360_PHASE7_3_PERFORMANCE_ARCHIVE_ROUTES_IMPORT
# /BYS360_PHASE7_4_PERFORMANCE_ARCHIVE_PERSONNEL_VISIBILITY_ROUTES_IMPORT
# /BYS360_PHASE7_5_PERFORMANCE_ARCHIVE_MANAGER_VISIBILITY_ROUTES_IMPORT
# /BYS360_FEEDBACK_AFTERCARE_PHASE1_ROUTES_IMPORT
# /BYS360_FEEDBACK_GUIDE_PHASE2_ROUTES_IMPORT
# /BYS360_FEEDBACK_INTEGRATION_PHASE3_ROUTES_IMPORT
# /BYS360_FEEDBACK_FOLLOWUP_PHASE4_ROUTES_IMPORT
# /BYS360_FEEDBACK_FINAL_GATE_PHASE5_ROUTES_IMPORT
# /BYS360_FEEDBACK_CORPORATE_CLEANUP_PHASE6_ROUTES_IMPORT
# /BYS360_FEEDBACK_PIPELINE_ROUTES_IMPORT
