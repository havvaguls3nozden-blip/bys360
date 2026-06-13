from __future__ import annotations



from datetime import date, datetime


def period_schedule_snapshot(period) -> dict[str, object]:
    if not period:
        return {
            'evaluation_start_date': None,
            'evaluation_end_date': None,
            'evaluation_due_days': None,
            'is_open_today': False,
        }
    return {
        'evaluation_start_date': getattr(period, 'evaluation_window_start', None).isoformat() if getattr(period, 'evaluation_window_start', None) else None,
        'evaluation_end_date': getattr(period, 'evaluation_window_end', None).isoformat() if getattr(period, 'evaluation_window_end', None) else None,
        'evaluation_due_days': getattr(period, 'evaluation_due_days_effective', None),
        'is_open_today': bool(period.is_evaluation_open_on(date.today())),
    }


def build_due_date_for_period(period, assigned_at: datetime | None = None):
    if not period:
        return None
    return period.build_due_datetime(assigned_at=assigned_at)