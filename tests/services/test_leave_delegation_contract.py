from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def test_leave_delegation_gate_documents_same_level_delegate_and_employee_modes() -> None:
    source = read("app/services/performance/leave_delegation_gate.py")

    required_tokens = [
        "same_level_delegate_or_uncovered_warning",
        "employee_leave_modes",
        "exclude",
        "partial",
        "informational",
        "audit_events",
        "delegated",
        "uncovered",
        "exempted",
        "simulate_employee_performance_mode",
        "simulate_effective_evaluator",
        "simulate_assignment_levels",
    ]

    missing = [token for token in required_tokens if token not in source]
    assert not missing, "Eksik izin/devamsızlık/vekâlet gate sözleşmesi: " + ", ".join(missing)


def test_leave_delegation_runtime_sources_keep_required_tokens() -> None:
    delegation_source = read("app/services/performance/delegation.py")
    effective_chain_source = read("app/services/performance/assignment_effective_chain.py")
    assignments_source = read("app/services/performance/assignments.py")

    required_by_file = {
        "delegation.py": [
            "resolve_effective_evaluator",
            "get_active_delegate",
            'reason_type="delegated"',
            'reason_type="delegation_missing"',
            '"exclude"',
            '"partial"',
            '"informational"',
        ],
        "assignment_effective_chain.py": [
            "resolve_employee_performance_mode",
            'performance_mode == "exclude"',
            'reason_type="excluded_due_leave"',
            "effective_chain[level]",
        ],
        "assignments.py": [
            "delegation_id",
            "assignment_source",
            "coverage_note",
            "coverage_resolutions",
        ],
    }

    haystacks = {
        "delegation.py": delegation_source,
        "assignment_effective_chain.py": effective_chain_source,
        "assignments.py": assignments_source,
    }

    missing: list[str] = []
    for name, tokens in required_by_file.items():
        for token in tokens:
            if token not in haystacks[name]:
                missing.append(f"{name}::{token}")

    assert not missing, "Eksik izin/devamsızlık/vekâlet runtime izi: " + ", ".join(missing)
