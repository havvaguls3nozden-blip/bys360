"""Behavior-lock for TD-CAND-006's closure.

The registry item described a dangling TODO in app/performance/task_routes.py
("index + partition lazim ama migration bekliyor") with no query it was
textually attached to. Forensic investigation traced the only plausible
target -- clear_period_task_records()'s single-predicate period_id/
evaluation_id filters against PerformanceEvaluation, PerformanceEvaluationItem,
EvaluationAssignment, and AssignmentCoverageLog -- and found every one of
those columns already indexed: 3 via composite indexes from migration
b4c2d1e9f005, the 4th (AssignmentCoverageLog.period_id, single-predicate
query, single-column index is sufficient) via migration e6b7d4c2f107. Both
are confirmed ancestors of the current Alembic head. No migration or
partitioning was needed; the comment was stale, not a real blocker.

This test locks in the reason the comment was safe to remove: it fails if
any of these four columns ever loses its index, which is exactly the
regression this closure needs to guard against.

pytestmark = ci_safe: pure metadata inspection, no DB/network/subprocess.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe


def test_performance_evaluation_period_id_is_indexed():
    from app.models.performance_models import PerformanceEvaluation
    assert PerformanceEvaluation.__table__.columns["period_id"].index is True


def test_performance_evaluation_item_evaluation_id_is_indexed():
    from app.models.performance_models import PerformanceEvaluationItem
    assert PerformanceEvaluationItem.__table__.columns["evaluation_id"].index is True


def test_evaluation_assignment_period_id_is_indexed():
    from app.models.performance_models import EvaluationAssignment
    assert EvaluationAssignment.__table__.columns["period_id"].index is True


def test_assignment_coverage_log_period_id_is_indexed():
    from app.models.performance_models import AssignmentCoverageLog
    assert AssignmentCoverageLog.__table__.columns["period_id"].index is True


def test_task_routes_no_longer_contains_stale_index_partition_todo():
    """The specific TODO comment TD-CAND-006 tracked must be gone -- removed
    only because the underlying concern was proven resolved, not as a
    documentation-only edit."""
    import pathlib
    content = pathlib.Path("app/performance/task_routes.py").read_text(encoding="utf-8")
    assert "index + partition lazım ama migration bekliyor" not in content
