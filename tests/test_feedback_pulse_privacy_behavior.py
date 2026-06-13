from __future__ import annotations

import ast
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def _load_pure_helper():
    source = Path("app/services/feedback_service.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    helper = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "_build_pulse_risk_users_from_rows"
    )
    code = ast.unparse(helper)
    namespace = {
        "defaultdict": defaultdict,
        "date": date,
        "timedelta": timedelta,
        "Any": Any,
    }
    exec(code, namespace)
    return namespace["_build_pulse_risk_users_from_rows"]


def test_anonymous_pulse_entries_never_become_named_risk_users():
    build_risk_users = _load_pure_helper()
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
    build_risk_users = _load_pure_helper()
    today = date(2026, 4, 18)
    rows = [
        SimpleNamespace(user_id=5, is_anonymous=False, mood_value=1, entry_date=today - timedelta(days=3)),
        SimpleNamespace(user_id=5, is_anonymous=False, mood_value=4, entry_date=today - timedelta(days=2)),
        SimpleNamespace(user_id=5, is_anonymous=False, mood_value=1, entry_date=today - timedelta(days=1)),
        SimpleNamespace(user_id=5, is_anonymous=False, mood_value=1, entry_date=today),
    ]

    assert build_risk_users(rows, {5: SimpleNamespace(full_name="Test Personeli")}, minimum_streak=3) == []
