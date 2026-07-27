from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

# BYS360 Phase 8: previously loaded via ast.parse + exec() of the source text
# to avoid importing app/services/feedback_service.py's wider dependency
# chain (app.extensions.db, app.models, notification bridge). Verified
# (2026-07-27) that a plain import carries no app-context/DB requirement --
# _build_pulse_risk_users_from_rows is a pure function -- and contributes
# real, measurable app/ coverage instead of 0% (exec()'d code is invisible
# to coverage.py because its co_filename is "<string>", not the real file).
from app.services.feedback_service import _build_pulse_risk_users_from_rows as build_risk_users


def test_anonymous_pulse_entries_never_become_named_risk_users():
    today = date(2026, 4, 18)
    rows = [
        SimpleNamespace(user_id=1, is_anonymous=True, mood_value=1, entry_date=today - timedelta(days=2)),
        SimpleNamespace(user_id=1, is_anonymous=True, mood_value=1, entry_date=today - timedelta(days=1)),
        SimpleNamespace(user_id=1, is_anonymous=True, mood_value=1, entry_date=today),
        SimpleNamespace(user_id=2, is_anonymous=False, mood_value=1, entry_date=today - timedelta(days=2)),
        SimpleNamespace(user_id=2, is_anonymous=False, mood_value=2, entry_date=today - timedelta(days=1)),
        SimpleNamespace(user_id=2, is_anonymous=False, mood_value=1, entry_date=today),
    ]
    users = {
        1: SimpleNamespace(full_name="Anonim Kişi"),
        2: SimpleNamespace(full_name="Görünen Personel"),
    }

    risk_users = build_risk_users(rows, users, minimum_streak=3)

    assert risk_users == [{"user_id": 2, "name": "Görünen Personel", "max_streak": 3}]


def test_named_risk_streak_breaks_when_mood_recovers():
    today = date(2026, 4, 18)
    rows = [
        SimpleNamespace(user_id=5, is_anonymous=False, mood_value=1, entry_date=today - timedelta(days=3)),
        SimpleNamespace(user_id=5, is_anonymous=False, mood_value=4, entry_date=today - timedelta(days=2)),
        SimpleNamespace(user_id=5, is_anonymous=False, mood_value=1, entry_date=today - timedelta(days=1)),
        SimpleNamespace(user_id=5, is_anonymous=False, mood_value=1, entry_date=today),
    ]

    assert build_risk_users(rows, {5: SimpleNamespace(full_name="Test Personeli")}, minimum_streak=3) == []
