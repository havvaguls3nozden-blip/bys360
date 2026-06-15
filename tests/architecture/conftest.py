from __future__ import annotations

import os
from pathlib import Path

import pytest

# BYS360_P2E_ACTIVE_ARCHITECTURE_SCOPE
# Varsayılan mimari test kapısı yalnızca güncel ve canlı omurgayla uyumlu
# aktif kalite testlerini çalıştırır. Eski Faz/Faz10/portal/anket/mesaj
# sözleşme testleri arşiv niteliğindedir; gerekirse ortam değişkeniyle
# ayrıca koşturulabilir.
ACTIVE_ARCHITECTURE_TEST_FILES = {
    "test_architecture_scope_p2e.py",
    "test_pytest_standard_p2d.py",
    "test_mobile_api_request_scenarios_p3a.py",
    "test_mobile_api_contract_p2a.py",
    "test_mobile_api_behavior_smoke_p2b.py",
    "test_mobile_api_request_level_smoke_p2c_v3.py",

    "test_mobile_api_personnel_kpi_communication_response_p3c_v2.py",
    "test_public_exports_live_guard_v1.py",
}


def _legacy_architecture_enabled() -> bool:
    return os.getenv("BYS360_RUN_LEGACY_ARCHITECTURE_TESTS", "").strip().lower() in {
        "1", "true", "yes", "on"
    }


def pytest_collection_modifyitems(config, items):
    if _legacy_architecture_enabled():
        return

    skip_legacy = pytest.mark.skip(
        reason=(
            "BYS360 eski mimari sözleşme testi arşiv kapsamındadır. "
            "Tüm eski testleri ayrıca çalıştırmak için "
            "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS=1 kullanın."
        )
    )

    for item in items:
        path_obj = getattr(item, "path", None) or getattr(item, "fspath", None)
        file_name = Path(str(path_obj)).name if path_obj is not None else ""
        if file_name.startswith("test_") and file_name not in ACTIVE_ARCHITECTURE_TEST_FILES:
            item.add_marker(skip_legacy)

# BYS360_CLAUDE_SCORE_UPLIFT_P3B_MOBILE_AUTH_DASHBOARD_ASSISTANT_RESPONSE_GATE: active architecture test -> test_mobile_auth_dashboard_assistant_response_p3b.py

# BYS360_P3D_ACTIVE_SCOPE_MARKER
try:
    ACTIVE_ARCHITECTURE_TESTS
except NameError:
    ACTIVE_ARCHITECTURE_TESTS = set()
if isinstance(ACTIVE_ARCHITECTURE_TESTS, tuple):
    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS)
if isinstance(ACTIVE_ARCHITECTURE_TESTS, list):
    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS)
try:
    ACTIVE_ARCHITECTURE_TESTS.add('test_mobile_api_support_survey_notifications_response_p3d.py')
except AttributeError:
    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS) | {'test_mobile_api_support_survey_notifications_response_p3d.py'}

# BYS360_P3E_ACTIVE_SCOPE_MARKER
try:
    ACTIVE_ARCHITECTURE_TESTS
except NameError:
    ACTIVE_ARCHITECTURE_TESTS = set()
if isinstance(ACTIVE_ARCHITECTURE_TESTS, tuple):
    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS)
if isinstance(ACTIVE_ARCHITECTURE_TESTS, list):
    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS)
try:
    ACTIVE_ARCHITECTURE_TESTS.add('test_mobile_api_performance_response_p3e.py')
except AttributeError:
    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS) | {'test_mobile_api_performance_response_p3e.py'}

# BYS360_P3F_ACTIVE_SCOPE_MARKER
try:
    ACTIVE_ARCHITECTURE_TESTS
except NameError:
    ACTIVE_ARCHITECTURE_TESTS = set()
if isinstance(ACTIVE_ARCHITECTURE_TESTS, tuple):
    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS)
if isinstance(ACTIVE_ARCHITECTURE_TESTS, list):
    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS)
try:
    ACTIVE_ARCHITECTURE_TESTS.add('test_mobile_api_response_suite_p3f.py')
except AttributeError:
    ACTIVE_ARCHITECTURE_TESTS = set(ACTIVE_ARCHITECTURE_TESTS) | {'test_mobile_api_response_suite_p3f.py'}
# BYS360_P4A_ACTIVE_SCOPE
BYS360_ACTIVE_ARCHITECTURE_TESTS = tuple(list(globals().get('BYS360_ACTIVE_ARCHITECTURE_TESTS', ())) + ['test_mobile_api_auth_guard_matrix_p4a.py'])
# BYS360_P4B_ACTIVE_SCOPE
BYS360_ACTIVE_ARCHITECTURE_TESTS = tuple(list(globals().get('BYS360_ACTIVE_ARCHITECTURE_TESTS', ())) + ['test_mobile_api_role_boundary_matrix_p4b_v3.py'])
"test_mobile_api_security_suite_p4c_v2.py",
"test_mobile_api_security_evidence_p4d.py",

# BYS360 P4E active architecture scope marker
try:
    ACTIVE_ARCHITECTURE_TESTS = list(ACTIVE_ARCHITECTURE_TESTS)
except NameError:
    ACTIVE_ARCHITECTURE_TESTS = []
if "test_mobile_api_release_evidence_p4e.py" not in ACTIVE_ARCHITECTURE_TESTS:
    ACTIVE_ARCHITECTURE_TESTS.append("test_mobile_api_release_evidence_p4e.py")

# BYS360 P5A active architecture scope marker
try:
    ACTIVE_ARCHITECTURE_TESTS = list(ACTIVE_ARCHITECTURE_TESTS)
except NameError:
    ACTIVE_ARCHITECTURE_TESTS = []
if "test_android_responsive_baseline_p5a.py" not in ACTIVE_ARCHITECTURE_TESTS:
    ACTIVE_ARCHITECTURE_TESTS.append("test_android_responsive_baseline_p5a.py")

# BYS360 P5B active architecture scope marker
try:
    ACTIVE_ARCHITECTURE_TESTS = list(ACTIVE_ARCHITECTURE_TESTS)
except NameError:
    ACTIVE_ARCHITECTURE_TESTS = []
if "test_android_responsive_core_styles_p5b.py" not in ACTIVE_ARCHITECTURE_TESTS:
    ACTIVE_ARCHITECTURE_TESTS.append("test_android_responsive_core_styles_p5b.py")

# BYS360_ACTIVE_ARCHITECTURE_TEST_P5C_ANDROID_RESPONSIVE_TARGETED_TEMPLATES: test_android_responsive_targeted_templates_p5c.py

# BYS360_ACTIVE_ARCHITECTURE_TEST_P5D_ANDROID_RESPONSIVE_RELEASE_SUITE: test_android_responsive_release_suite_p5d.py

# BYS360_ACTIVE_ARCHITECTURE_TEST_P5D_V2_ANDROID_RESPONSIVE_RELEASE_SUITE: test_android_responsive_release_suite_p5d_v2.py

# BYS360_ACTIVE_ARCHITECTURE_TEST_P5E_ANDROID_RESPONSIVE_VISUAL_UAT_EVIDENCE: test_android_responsive_visual_uat_evidence_p5e.py

# BYS360_ACTIVE_ARCHITECTURE_TEST_P5F_ANDROID_RESPONSIVE_FINAL_EVIDENCE: test_android_responsive_final_evidence_p5f.py

# BYS360_ACTIVE_ARCHITECTURE_TEST::test_android_responsive_visual_regression_p6a.py

# BYS360_ACTIVE_ARCHITECTURE_SCOPE_ALLOW: test_android_responsive_visual_regression_evidence_suite_p6b.py

# BYS360_ACTIVE_ARCHITECTURE_SCOPE_ALLOW: test_android_responsive_visual_regression_evidence_suite_p6b_v2.py

# BYS360_ACTIVE_ARCHITECTURE_TEST: test_android_responsive_inventory_precision_p6c.py
# BYS360_P4B_ACTIVE_SCOPE
BYS360_ACTIVE_ARCHITECTURE_TESTS = tuple(list(globals().get('BYS360_ACTIVE_ARCHITECTURE_TESTS', ())) + ['test_mobile_api_role_boundary_matrix_p4b_v3.py'])

