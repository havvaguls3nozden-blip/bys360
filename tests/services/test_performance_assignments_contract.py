from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def test_performance_assignments_keeps_coverage_and_delegation_contracts() -> None:
    source = read("app/services/performance/assignments.py")

    required_tokens = [
        "ensure_evaluation_record",
        "EvaluationAssignment",
        "assignment_source",
        "coverage_note",
        "coverage_resolutions",
        '"delegated": 0',
        '"exempted": 0',
        '"uncovered": 0',
        "build_assignment_log_summary",
        "build_assignment_unit_summary",
        "resolve_effective_manager",
        "apply_availability_snapshot_to_evaluation",
    ]

    missing = [token for token in required_tokens if token not in source]
    assert not missing, "Eksik performans assignment sözleşme izi: " + ", ".join(missing)


def test_performance_assignments_does_not_turn_special_info_into_fatal_noise() -> None:
    source = read("app/services/performance/assignments.py")

    required_tokens = [
        "is_informational_special_case",
        "_normalize_reason_text",
        "hukuk musavirligi",
        "tek amir",
        "3. amir yorumcu modunda",
        "vekalet nedeniyle gorev ayni seviyede vekile yonlendirildi",
    ]

    missing = [token for token in required_tokens if token not in source]
    assert not missing, "Eksik info-only/special-case sözleşme izi: " + ", ".join(missing)
