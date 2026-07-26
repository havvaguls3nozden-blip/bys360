from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from typing import cast

import pytest

from app.models import PerformanceEvaluation, PerformancePeriod
from app.services.performance import low_score_process_service as svc

# _period_year/_is_completed/is_low_score_evaluation all read their argument
# purely through getattr(x, attr, default) (verified in
# app/services/performance/low_score_process_service.py), so a SimpleNamespace
# exposing only the handful of attributes each test needs is a faithful,
# duck-typed stand-in for the real PerformancePeriod/PerformanceEvaluation
# instance. The casts below tell mypy that, without touching production
# signatures.


def _phase4t_contains_value(value, expected) -> bool:
    if value == expected:
        return True
    if isinstance(value, dict):
        return any(_phase4t_contains_value(item, expected) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_phase4t_contains_value(item, expected) for item in value)
    return False


def test_phase4t_safe_normalize_actor_and_period_helpers() -> None:
    assert svc._safe_float("69.5") == 69.5
    assert svc._safe_float(None, default=7.0) == 7.0
    assert svc._safe_float("bozuk", default=3.5) == 3.5

    assert svc._normalize("  Tamamlandı  ") == "tamamlandı"
    assert svc._normalize(None) == ""

    assert svc._actor_id(SimpleNamespace(id="42")) == 42
    assert svc._actor_id("17") == 17
    assert svc._actor_id("bozuk") is None
    assert svc._actor_id(None) is None

    assert svc._period_year(cast(PerformancePeriod, SimpleNamespace(end_date=date(2026, 7, 31)))) == 2026
    assert svc._period_year(cast(PerformancePeriod, SimpleNamespace(start_date=date(2025, 1, 1)))) == 2025
    assert isinstance(svc._period_year(None), int)


def test_phase4t_completed_guard_rejects_draft_pending_and_returned_values() -> None:
    assert svc._is_completed(None) is False

    assert svc._is_completed(cast(PerformanceEvaluation, SimpleNamespace(status="draft"))) is False
    assert svc._is_completed(cast(PerformanceEvaluation, SimpleNamespace(status="pending"))) is False
    assert svc._is_completed(cast(PerformanceEvaluation, SimpleNamespace(status="iade_edildi"))) is False
    assert svc._is_completed(cast(PerformanceEvaluation, SimpleNamespace(workflow_status="returned_by_president"))) is False

    assert svc._is_completed(cast(PerformanceEvaluation, SimpleNamespace(status="completed"))) is True
    assert svc._is_completed(cast(PerformanceEvaluation, SimpleNamespace(workflow_status="tamamlandı"))) is True
    assert svc._is_completed(cast(PerformanceEvaluation, SimpleNamespace(publish_status="published"))) is True
    assert svc._is_completed(cast(PerformanceEvaluation, SimpleNamespace(level_1_completed=True))) is True


def test_phase4t_low_score_evaluation_detection_for_numbers_and_objects() -> None:
    assert svc.is_low_score_evaluation(None) is False
    assert svc.is_low_score_evaluation(0) is False
    assert svc.is_low_score_evaluation(69.99) is True
    assert svc.is_low_score_evaluation(70) is False

    completed_low = cast(PerformanceEvaluation, SimpleNamespace(
        status="completed",
        workflow_status="",
        approval_status="",
        publish_status="",
        final_total_100=69,
        level_1_completed=False,
    ))
    assert svc.is_low_score_evaluation(completed_low) is True

    completed_not_low = cast(PerformanceEvaluation, SimpleNamespace(
        status="completed",
        workflow_status="",
        approval_status="",
        publish_status="",
        final_total_100=70,
        level_1_completed=False,
    ))
    assert svc.is_low_score_evaluation(completed_not_low) is False

    draft_low = cast(PerformanceEvaluation, SimpleNamespace(
        status="draft",
        workflow_status="",
        approval_status="",
        publish_status="",
        final_total_100=50,
        level_1_completed=False,
    ))
    assert svc.is_low_score_evaluation(draft_low) is False


def test_phase4t_step_metadata_and_sequence_type_helpers() -> None:
    assert "Başkan" in svc._event_title("president_approval")
    assert svc._event_title("bilinmeyen") == "bilinmeyen"

    assert svc._event_sort("president_approval") == 40
    assert svc._event_sort("bilinmeyen") == 999

    assert svc._process_type_for_sequence(1) == "first_low_score_warning"
    assert svc._process_type_for_sequence(2) == "second_low_score_admin_process"
    assert svc._process_type_for_sequence(0) == "first_low_score_warning"


def test_phase4t_low_score_period_summary_as_dict_without_constructor_assumption() -> None:
    summary_obj = object.__new__(svc.LowScorePeriodSummary)
    summary_obj.total = 6
    summary_obj.pending_president = 1
    summary_obj.pending_hr = 2
    summary_obj.pending_warning = 3
    summary_obj.pending_admin_process = 4
    summary_obj.ready_for_publish = 5

    assert summary_obj.as_dict() == {
        "total": 6,
        "pending_president": 1,
        "pending_hr": 2,
        "pending_warning": 3,
        "pending_admin_process": 4,
        "ready_for_publish": 5,
    }


def test_phase4t_name_timeline_and_row_builders_are_stable() -> None:
    assert svc._full_name(None) == "-"
    assert svc._full_name(SimpleNamespace(full_name="Ada Lovelace")) == "Ada Lovelace"
    assert svc._full_name(SimpleNamespace(ad="Ada", soyad="Lovelace")) == "Ada Lovelace"
    assert svc._full_name(SimpleNamespace(ad="", soyad="")) == "-"

    assert svc.build_process_timeline(None) == []

    process = SimpleNamespace(
        id=10,
        employee=SimpleNamespace(full_name="Personel Bir"),
        employee_id=20,
        final_total_100=62.5,
        status="president_approval_pending",
        process_type="first_low_score_warning",
        president_approved_at=None,
        president_rejected_at=None,
        warning_recorded_at=None,
        administrative_process_started_at=None,
        president_approval_note="Onay notu",
    )

    rows = svc.build_low_score_process_rows([process])

    assert len(rows) == 1
    assert _phase4t_contains_value(rows, 10)
    assert _phase4t_contains_value(rows, "Onay notu")


def test_phase4t_status_humanizers_cover_known_and_unknown_values() -> None:
    assert "Başkan" in svc.humanize_process_status(None)
    assert "Başkan" in svc.humanize_process_status("president_approval_pending")
    assert "Tekrarlayan" in svc.humanize_process_status("second_low_repeat")
    assert svc.humanize_process_status("custom_status") == "Custom Status"

    assert "Süreç" in svc.humanize_low_score_status(None)
    assert "Başkan" in svc.humanize_low_score_status("president_approval_pending")
    assert "Tekrarlayan" in svc.humanize_low_score_status("second_low_score_process_started")
    assert svc.humanize_low_score_status("custom_status") == "Custom Status"


def test_phase4t_publish_block_reason_for_direct_process_states() -> None:
    high_score_process = SimpleNamespace(final_total_100=80)
    assert svc.get_low_score_publish_block_reason(process=high_score_process, ensure=False) is None

    rejected = SimpleNamespace(
        final_total_100=60,
        president_rejected_at=object(),
        president_approved_at=None,
        process_type="first_low_score_warning",
        administrative_process_started_at=None,
        warning_recorded_at=None,
    )
    assert "iade" in svc.get_low_score_publish_block_reason(process=rejected, ensure=False).lower()

    pending = SimpleNamespace(
        final_total_100=60,
        president_rejected_at=None,
        president_approved_at=None,
        process_type="first_low_score_warning",
        administrative_process_started_at=None,
        warning_recorded_at=None,
    )
    assert "Başkan" in svc.get_low_score_publish_block_reason(process=pending, ensure=False)

    first_without_warning = SimpleNamespace(
        final_total_100=60,
        president_rejected_at=None,
        president_approved_at=object(),
        process_type="first_low_score_warning",
        administrative_process_started_at=None,
        warning_recorded_at=None,
    )
    assert "İlk" in svc.get_low_score_publish_block_reason(process=first_without_warning, ensure=False)

    released = SimpleNamespace(
        final_total_100=60,
        president_rejected_at=None,
        president_approved_at=object(),
        process_type="first_low_score_warning",
        administrative_process_started_at=None,
        warning_recorded_at=object(),
    )
    assert svc.get_low_score_publish_block_reason(process=released, ensure=False) is None


def test_phase4t_auto_transition_shortcuts_with_process_resolution_patched(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "_bys360_lh13_get_process", lambda value: value)

    assert svc.auto_record_first_low_score_warning(None) is None
    assert svc.auto_start_second_low_score_process(None) is None

    already_warning = SimpleNamespace(warning_recorded_at=object())
    assert svc.auto_record_first_low_score_warning(already_warning) is already_warning

    already_admin = SimpleNamespace(administrative_process_started_at=object())
    assert svc.auto_start_second_low_score_process(already_admin) is already_admin

