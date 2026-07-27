from __future__ import annotations

from typing import Any


def test_save_pulse_entry_schedules_async_refresh_without_inline(monkeypatch):
    import app.services.feedback_service as svc

    calls: list[tuple[Any, ...]] = []

    class FakeSession:
        def add(self, obj): pass
        def commit(self): pass
        def flush(self): pass

    class FakeEntry:
        def __init__(self):
            self.mood_value = None
            self.mood_label = None
            self.short_note = None
            self.is_anonymous = None

    monkeypatch.setattr(svc, "get_today_pulse_entry", lambda user: FakeEntry())
    monkeypatch.setattr(svc, "_clear_pulse_cache_for_unit", lambda unit_id: calls.append(("clear", unit_id)))
    monkeypatch.setattr(svc, "_enqueue_pulse_analytics_refresh", lambda unit_id, days=30: calls.append(("enqueue", unit_id, days)))
    monkeypatch.setattr(svc.db, "session", FakeSession())

    user = type("User", (), {"id": 10, "organization_unit_id": 33})()
    entry = svc.save_pulse_entry(user=user, mood_value=2, short_note="Bugün zorlandım", is_anonymous=True)

    assert entry.mood_value == 2
    assert entry.is_anonymous is True
    assert ("clear", 33) in calls
    assert ("enqueue", 33, 30) in calls
