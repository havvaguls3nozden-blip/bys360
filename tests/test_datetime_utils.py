from app.core.datetime_utils import utc_now, utc_now_aware


def test_utc_now_returns_datetime():
    value = utc_now()
    assert value.tzinfo is None


def test_utc_now_aware_returns_timezone_aware_datetime():
    value = utc_now_aware()
    assert value.tzinfo is not None
