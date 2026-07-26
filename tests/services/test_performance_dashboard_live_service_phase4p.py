from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
from typing import cast

import pytest

from app.models import PerformancePeriod
from app.services import performance_dashboard_live_service as svc


def test_phase4p_safe_number_helpers_handle_valid_and_invalid_values() -> None:
    assert svc._safe_int("7") == 7
    assert svc._safe_int(None) == 0
    assert svc._safe_int("bozuk", default=5) == 5

    assert svc._safe_float("2.5") == 2.5
    assert svc._safe_float(None) == 0.0
    assert svc._safe_float("bozuk", default=1.25) == 1.25

    assert svc._pct(1, 4) == 25.0
    assert svc._pct(1, 0) == 0.0
    assert svc._pct(cast(float, "bozuk"), 2) == 0.0


def test_phase4p_period_label_and_range_are_safe() -> None:
    assert svc._period_label(None) == "Aktif dönem yok"

    named_period = cast(PerformancePeriod, SimpleNamespace(id=9, title="2026 Performans", name=None))
    assert svc._period_label(named_period) == "2026 Performans"

    fallback_period = cast(PerformancePeriod, SimpleNamespace(id=42, title=None, name=None))
    assert svc._period_label(fallback_period) == "Dönem #42"

    dated_period = cast(PerformancePeriod, SimpleNamespace(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    ))
    period_range = svc._period_range(dated_period)
    assert "01.01.2026" in period_range
    assert "31.01.2026" in period_range

    assert svc._period_range(None) == "Dönem seçildiğinde veriler otomatik güncellenir."

    malformed_period = cast(PerformancePeriod, SimpleNamespace(start_date="baslangic", end_date="bitis"))
    malformed_range = svc._period_range(malformed_period)
    assert "baslangic" in malformed_range
    assert "bitis" in malformed_range


def test_phase4p_scope_ids_prefers_existing_dashboard_scope() -> None:
    user = SimpleNamespace(id=99)

    result = svc._scope_ids(
        user,
        {
            "dashboard_scope": {
                "scope_user_ids": ["1", 2, None, ""],
            }
        },
    )

    assert result == [1, 2]


def test_phase4p_scope_ids_falls_back_to_current_user_when_scope_builder_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    user = SimpleNamespace(id="77")

    def fail_scope(*args, **kwargs):
        raise RuntimeError("scope yok")

    monkeypatch.setattr(svc, "build_user_scope_context", fail_scope)
    monkeypatch.setattr(svc, "safe_db_rollback", lambda: None)

    assert svc._scope_ids(user, {}) == [77]


def test_phase4p_total_and_completed_evaluation_shortcuts_avoid_queries(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_query(*args, **kwargs):
        raise AssertionError("base_context varken query cagrilmamali")

    monkeypatch.setattr(svc, "_evaluation_query", fail_query)

    assert svc._total_evaluations(None, [], {"total_evaluations": "12"}) == 12
    assert svc._completed_evaluations(None, [], {"completed_evaluations": "9"}) == 9


def test_phase4p_approval_status_builds_counts_percentages_and_gradient() -> None:
    result = svc._approval_status(
        total=10,
        published=3,
        president_pending=2,
        returned=1,
    )

    assert result["total"] == 10
    assert result["gradient"].startswith("conic-gradient(")

    rows_by_key = {row["key"]: row for row in result["rows"]}

    assert rows_by_key["published"]["count"] == 3
    assert rows_by_key["published"]["percent"] == 30.0

    assert rows_by_key["president"]["count"] == 2
    assert rows_by_key["president"]["percent"] == 20.0

    assert rows_by_key["returned"]["count"] == 1
    assert rows_by_key["returned"]["percent"] == 10.0

    assert rows_by_key["pending"]["count"] == 4
    assert rows_by_key["pending"]["percent"] == 40.0


def test_phase4p_format_time_handles_today_yesterday_old_and_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "utc_now", lambda: datetime(2026, 7, 11, 10, 0))

    assert svc._format_time(None) == "-"
    assert svc._format_time(datetime(2026, 7, 11, 9, 30)) == "Bugün 09:30"
    assert svc._format_time(datetime(2026, 7, 10, 9, 30)) == "Dün 09:30"
    assert svc._format_time(datetime(2026, 7, 9, 9, 30)) == "09.07.2026"


def test_phase4p_trend_polyline_and_decision_note_outputs_are_stable() -> None:
    assert svc._trend_polyline(
        [
            {"x": 1, "y": 2},
            {"x": 3, "y": 4},
        ]
    ) == "1,2 3,4"

    assert "düşük performans" in svc._decision_note(
        total=10,
        completion_rate=50.0,
        low_count=2,
        overdue_count=0,
        pending_president=0,
    )

    assert "geciken amir" in svc._decision_note(
        total=10,
        completion_rate=50.0,
        low_count=0,
        overdue_count=2,
        pending_president=0,
    )

    assert "üst onay" in svc._decision_note(
        total=10,
        completion_rate=50.0,
        low_count=0,
        overdue_count=0,
        pending_president=2,
    )

    assert "Dönem kapanışı" in svc._decision_note(
        total=10,
        completion_rate=95.0,
        low_count=0,
        overdue_count=0,
        pending_president=0,
    )

    assert "canlı veriye" in svc._decision_note(
        total=0,
        completion_rate=0.0,
        low_count=0,
        overdue_count=0,
        pending_president=0,
    )


def _phase4q_contains_value(value, expected) -> bool:
    if value == expected:
        return True
    if isinstance(value, dict):
        return any(_phase4q_contains_value(item, expected) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_phase4q_contains_value(item, expected) for item in value)
    return False


def test_phase4q_build_live_performance_dashboard_context_uses_safe_aggregators(monkeypatch: pytest.MonkeyPatch) -> None:
    period = SimpleNamespace(
        id=33,
        title="2026 Canlı Performans",
        name=None,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 31),
    )
    user = SimpleNamespace(id=77)

    monkeypatch.setattr(svc, "_active_period", lambda: period)
    monkeypatch.setattr(svc, "_scope_ids", lambda user, base_context: [77, 88])

    monkeypatch.setattr(svc, "_total_evaluations", lambda period_id, scope_user_ids, base_context: 12)
    monkeypatch.setattr(svc, "_completed_evaluations", lambda period_id, scope_user_ids, base_context: 9)
    monkeypatch.setattr(svc, "_low_score_count", lambda period_id, scope_user_ids: 2)
    monkeypatch.setattr(svc, "_published_count", lambda period_id, scope_user_ids: 6)
    monkeypatch.setattr(svc, "_president_pending_count", lambda period_id, scope_user_ids: 3)
    monkeypatch.setattr(svc, "_returned_count", lambda period_id, scope_user_ids: 1)

    trend_points = [
        {"label": "01.07", "value": 3, "x": 1, "y": 90},
        {"label": "31.07", "value": 9, "x": 99, "y": 10},
    ]

    monkeypatch.setattr(svc, "_completion_trend", lambda period, scope_user_ids, total: trend_points)
    monkeypatch.setattr(
        svc,
        "_category_averages",
        lambda period_id, scope_user_ids: [
            {"label": "Teknik", "average": 86.5},
        ],
    )
    monkeypatch.setattr(
        svc,
        "_overdue_managers",
        lambda period_id, scope_user_ids: [
            {"name": "Geciken Amir", "count": 2},
        ],
    )
    monkeypatch.setattr(
        svc,
        "_risk_matrix",
        lambda period_id, scope_user_ids: {
            "total": 4,
            "rows": [{"label": "Risk", "count": 4}],
        },
    )
    monkeypatch.setattr(
        svc,
        "_low_score_density",
        lambda period_id, scope_user_ids: [
            {"label": "Birim A", "low": 2, "percent": 25.0},
        ],
    )
    monkeypatch.setattr(
        svc,
        "_recent_activity",
        lambda user_id, period_id, scope_user_ids: [
            {"title": "Son aktivite", "time": "Bugün 09:30"},
        ],
    )

    result = svc.build_live_performance_dashboard_context(
        user,
        {
            "dashboard_scope": {
                "scope_user_ids": [77, 88],
            }
        },
    )

    assert isinstance(result, dict)
    assert result

    # Ana toplayıcı fonksiyonun güvenli değerleri bağladığını doğrula.
    assert _phase4q_contains_value(result, "2026 Canlı Performans")
    assert _phase4q_contains_value(result, "01.07.2026 – 31.07.2026")
    assert _phase4q_contains_value(result, 12)
    assert _phase4q_contains_value(result, 9)
    assert _phase4q_contains_value(result, 75.0)
    assert _phase4q_contains_value(result, 2)
    assert _phase4q_contains_value(result, 3)
    assert _phase4q_contains_value(result, 1)
    assert _phase4q_contains_value(result, "1,90 99,10")
    assert _phase4q_contains_value(result, "Geciken Amir")
    assert _phase4q_contains_value(result, "Birim A")
    assert _phase4q_contains_value(result, "Son aktivite")
    assert _phase4q_contains_value(result, "2 düşük performans kaydı var; Başkan/üst onay ve gelişim takibi birlikte izlenmeli.")
