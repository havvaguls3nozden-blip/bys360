"""BYS360 Assistant V2 -- native response composer behavior contract.

Replaces the earlier LLM-based composer's test file (that whole
architecture was removed per the "BYS360 Native AI Only" product decision --
see response_composer.py's module docstring). These tests prove the native,
zero-AI-dependency composer produces real Turkish sentences built from
`result.data` -- not a canned string, not JSON dumped -- for the generic
list/dict/scalar cases, and that the flagship cross-module example produces
the exact phrasing the mandate specified.
"""
from __future__ import annotations

from typing import Any

import pytest

pytestmark = pytest.mark.ci_safe


def _result(**overrides: Any) -> Any:
    from app.services.assistant_v2.result_contract import (
        AssistantCapabilityResult,
        AssistantResultStatus,
    )

    defaults: dict[str, Any] = dict(
        status=AssistantResultStatus.DATA_FOUND,
        message="İstenen bilgi bulundu.",
        capability_key="performance_mgmt_list_active_periods",
        module_key="performance_mgmt",
        data=[{"id": 1, "title": "2026/1 Dönemi"}],
        source_label="Performans Dönemi Kaydı",
    )
    defaults.update(overrides)
    return AssistantCapabilityResult(**defaults)


@pytest.mark.parametrize(
    "status_name",
    ["NO_DATA", "ACCESS_DENIED", "CAPABILITY_UNAVAILABLE", "AMBIGUOUS_REQUEST", "SYSTEM_ERROR"],
)
def test_non_data_found_statuses_return_dispatcher_message_verbatim(status_name):
    from app.services.assistant_v2 import response_composer
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    status = getattr(AssistantResultStatus, status_name)
    result = _result(status=status, data=None, message=f"safe message for {status_name}")
    composed = response_composer.compose_response(result, question="herhangi bir soru")

    assert composed.answer_text == result.message
    assert composed.used_llm is False


def test_list_data_renders_real_count_and_item_labels_not_json():
    from app.services.assistant_v2 import response_composer

    result = _result(
        data=[
            {"id": 1, "title": "2026/1 Dönemi"},
            {"id": 2, "title": "2026/2 Dönemi"},
        ]
    )
    composed = response_composer.compose_response(result, question="aktif dönemleri göster")

    assert "2" in composed.answer_text
    assert "2026/1 Dönemi" in composed.answer_text
    assert "2026/2 Dönemi" in composed.answer_text
    assert "{" not in composed.answer_text  # never a raw JSON/dict dump


def test_empty_list_data_renders_no_data_phrase():
    from app.services.assistant_v2 import response_composer

    result = _result(data=[])
    composed = response_composer.compose_response(result, question="aktif dönemleri göster")

    assert "bulunamadı" in composed.answer_text


def test_dict_data_renders_key_value_summary():
    from app.services.assistant_v2 import response_composer

    result = _result(
        capability_key="settings_auth_summarize_role_permission_coverage",
        module_key="settings_auth",
        data={"admin": 42, "personel": 10},
    )
    composed = response_composer.compose_response(result, question="rol izin kapsama özeti")

    assert "42" in composed.answer_text
    assert "10" in composed.answer_text


def test_source_attribution_appended_to_answer():
    from app.services.assistant_v2 import response_composer

    result = _result(source_label="Performans Dönemi Kaydı")
    composed = response_composer.compose_response(result, question="aktif dönemleri göster")

    assert "Kaynak: Performans Dönemi Kaydı" in composed.answer_text


def test_unknown_capability_key_never_raises():
    """A capability_key that has been removed from the registry since the
    result was produced (edge case) must still render something safe, not
    crash the caller."""
    from app.services.assistant_v2 import response_composer

    result = _result(capability_key="this_capability_no_longer_exists")
    composed = response_composer.compose_response(result, question="x")

    assert composed.answer_text


# ---------------------------------------------------------------------------
# Cross-module flagship example
# ---------------------------------------------------------------------------


def test_cross_module_flagship_phrasing_matches_mandate_example():
    from app.services.assistant_v2 import response_composer
    from app.services.assistant_v2.cross_module_orchestrator import CrossModuleResult
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    result = CrossModuleResult(
        status=AssistantResultStatus.DATA_FOUND,
        message="İstenen bilgi bulundu.",
        data=[
            {"id": 1, "full_name": "Ayşe Yılmaz"},
            {"id": 2, "full_name": "Mehmet Demir"},
        ],
        contributing_capability_keys=(
            "personnel_hr_list_personnel",
            "performance_mgmt_list_incomplete_evaluations",
        ),
        contributing_module_keys=("personnel_hr", "performance_mgmt"),
        source_labels=("Personel Listesi", "Performans Değerlendirme Kaydı"),
    )
    composed = response_composer.compose_cross_module_response(result, question="birimimde eksik değerlendirmesi olanlar")

    assert "Biriminizde performans değerlendirmesi tamamlanmamış" in composed.answer_text
    assert "2 personel" in composed.answer_text
    assert "Ayşe Yılmaz" in composed.answer_text
    assert "Mehmet Demir" in composed.answer_text


def test_cross_module_denied_status_returns_message_verbatim():
    from app.services.assistant_v2 import response_composer
    from app.services.assistant_v2.cross_module_orchestrator import CrossModuleResult
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    result = CrossModuleResult(
        status=AssistantResultStatus.ACCESS_DENIED,
        message="denied message",
        contributing_capability_keys=("personnel_hr_list_personnel",),
        contributing_module_keys=("personnel_hr",),
    )
    composed = response_composer.compose_cross_module_response(result, question="x")

    assert composed.answer_text == "denied message"
