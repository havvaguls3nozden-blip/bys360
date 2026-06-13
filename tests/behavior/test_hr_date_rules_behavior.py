from __future__ import annotations

from datetime import date

from app.services.hr_date_rules import date_ranges_overlap


def test_leave_date_ranges_overlap_on_shared_day():
    assert date_ranges_overlap(date(2026, 4, 1), date(2026, 4, 5), date(2026, 4, 5), date(2026, 4, 7)) is True


def test_leave_date_ranges_do_not_overlap_when_separate():
    assert date_ranges_overlap(date(2026, 4, 1), date(2026, 4, 5), date(2026, 4, 6), date(2026, 4, 8)) is False


def test_invalid_ranges_are_not_treated_as_overlap():
    assert date_ranges_overlap(date(2026, 4, 5), date(2026, 4, 1), date(2026, 4, 2), date(2026, 4, 3)) is False
