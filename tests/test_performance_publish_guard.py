from app.services.performance.publish_guard import (
    build_publish_preflight_report,
    build_scorecard_visibility_summary,
    publish_preflight_has_blockers,
)


def test_publish_preflight_blocks_when_ready_count_zero():
    report = build_publish_preflight_report(
        period=object(),
        scorecard={"count": 5, "completed_count": 4, "published_count": 0},
        publish_summary={"ready_count": 0, "blocked_count": 4, "internal_preview_count": 4},
    )
    assert publish_preflight_has_blockers(report) is True


def test_scorecard_visibility_summary_counts_states():
    summary = build_scorecard_visibility_summary(
        {
            "count": 3,
            "rows": [
                {"visibility": {"publish_state": "published"}, "employee_viewed_at": object(), "employee_acknowledged_at": None},
                {"visibility": {"publish_state": "internal_preview"}, "employee_viewed_at": None, "employee_acknowledged_at": None},
                {"visibility": {"publish_state": "locked"}, "employee_viewed_at": None, "employee_acknowledged_at": object()},
            ],
        }
    )
    assert summary["employee_visible"] == 1
    assert summary["internal_preview"] == 1
    assert summary["locked"] == 1
    assert summary["viewed"] == 1
    assert summary["acknowledged"] == 1
