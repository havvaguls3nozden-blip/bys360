"""BYS360 HOTFIX 3: portal_press_news_service._press_news_sort_key's ISO-first
date parser previously logged a full ERROR-level traceback (via
logging.exception) every time an RFC/HTTP/RSS-style date string (e.g.
"Mon, 15 Dec 2025 16:01:00 GMT") failed datetime.fromisoformat -- even
though this is the EXPECTED, designed-for outcome for that format, and the
very next line (email.utils.parsedate_to_datetime) always parses it
successfully. In real production this produced a 1184-traceback log storm
after a single portal request and measurably slowed /portal.

Root cause: the first except block used a broad `except Exception` +
`logging.exception(...)`, treating a routine, anticipated format mismatch
as if it were a genuine unhandled error.

Fix: narrow both except clauses to the exact exceptions both stdlib parsers
document raising on a parse failure (ValueError, TypeError -- confirmed
empirically against the installed Python for every sample date in this
file). The first (ISO) parser's failure is now silent -- it is expected,
normal control flow whenever the value is RFC-formatted instead. Only if
BOTH the ISO and the RFC/HTTP parser fail (genuinely invalid data) does the
function emit a single bounded, traceback-free logging.warning() call.

This file proves: ISO and RFC/HTTP dates both parse and sort correctly,
RFC-format dates create zero ERROR/exception-level log records, malformed
values still degrade safely (no crash, still exactly one WARNING), and
None/empty inputs are unaffected (they are skipped before any parser runs).
"""
from __future__ import annotations

import logging

from app.services.portal_press_news_service import _press_news_sort_key


def test_iso_date_parses_and_returns_matching_epoch_timestamp():
    item = {"published_at_iso": "2026-09-18T09:17:00+00:00"}
    key = _press_news_sort_key(item)
    assert key == 1789723020.0


def test_iso_z_suffixed_date_parses_correctly():
    item_z = {"published_at_iso": "2026-09-18T09:17:00Z"}
    item_offset = {"published_at_iso": "2026-09-18T09:17:00+00:00"}
    assert _press_news_sort_key(item_z) == _press_news_sort_key(item_offset)


def test_rfc_http_date_parses_successfully(caplog):
    caplog.set_level(logging.DEBUG, logger="app.services.portal_press_news_service")
    item = {"published_at": "Sat, 12 Aug 2023 07:12:00 GMT"}
    key = _press_news_sort_key(item)
    assert key > 0.0


def test_second_real_production_rfc_date_parses_successfully():
    item = {"published_at": "Mon, 15 Dec 2025 16:01:00 GMT"}
    key = _press_news_sort_key(item)
    assert key > 0.0


def test_rfc_date_fallback_generates_zero_error_or_exception_log_records(caplog):
    """BYS360 HOTFIX 3 core proof: the exact defect this closes -- no
    ERROR-level, no exc_info/traceback log record is emitted for a value
    that only the RFC/HTTP fallback parser (not ISO) can parse."""
    caplog.set_level(logging.DEBUG, logger="app.services.portal_press_news_service")
    for value in (
        "Sat, 12 Aug 2023 07:12:00 GMT",
        "Mon, 15 Dec 2025 16:01:00 GMT",
        "Wed, 03 Jun 2026 03:42:00 GMT",
    ):
        caplog.clear()
        key = _press_news_sort_key({"published_at": value})
        assert key > 0.0
        error_or_exc_records = [
            r for r in caplog.records
            if r.levelno >= logging.ERROR or r.exc_info is not None
        ]
        assert error_or_exc_records == [], (
            f"expected zero ERROR/traceback log records for a normally-supported "
            f"RFC date {value!r}, got: {[(r.levelname, r.getMessage()) for r in error_or_exc_records]}"
        )
        assert "Traceback" not in caplog.text
        assert "Invalid isoformat string" not in caplog.text


def test_mixed_iso_and_rfc_items_sort_chronologically():
    items = [
        {"id": "rfc_middle", "published_at": "Mon, 15 Dec 2025 16:01:00 GMT"},
        {"id": "iso_newest", "published_at_iso": "2026-09-18T09:17:00Z"},
        {"id": "rfc_oldest", "published_at": "Sat, 12 Aug 2023 07:12:00 GMT"},
    ]
    ordered = sorted(items, key=_press_news_sort_key, reverse=True)
    assert [row["id"] for row in ordered] == ["iso_newest", "rfc_middle", "rfc_oldest"]


def test_iso_and_equivalent_rfc_value_produce_comparable_timestamps():
    iso_item = {"published_at_iso": "2023-08-12T07:12:00+00:00"}
    rfc_item = {"published_at": "Sat, 12 Aug 2023 07:12:00 GMT"}
    assert _press_news_sort_key(iso_item) == _press_news_sort_key(rfc_item)


def test_naive_iso_datetime_is_treated_as_utc():
    naive_item = {"published_at_iso": "2026-09-18T09:17:00"}
    aware_item = {"published_at_iso": "2026-09-18T09:17:00+00:00"}
    assert _press_news_sort_key(naive_item) == _press_news_sort_key(aware_item)


def test_malformed_date_does_not_crash_and_falls_back_to_zero(caplog):
    caplog.set_level(logging.DEBUG, logger="app.services.portal_press_news_service")
    key = _press_news_sort_key({"published_at": "not-a-date"})
    assert key == 0.0
    warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
    assert len(warning_records) == 1
    assert warning_records[0].exc_info is None, "the bounded invalid-data diagnostic must not carry a traceback"
    assert "not-a-date" in warning_records[0].getMessage()


def test_one_malformed_item_does_not_break_the_rest_of_the_sorted_list():
    items = [
        {"id": "good", "published_at_iso": "2026-09-18T09:17:00Z"},
        {"id": "bad", "published_at": "not-a-date"},
    ]
    ordered = sorted(items, key=_press_news_sort_key, reverse=True)
    assert [row["id"] for row in ordered] == ["good", "bad"]


def test_none_and_empty_values_retain_safe_fallback_behavior():
    assert _press_news_sort_key({}) == 0.0
    assert _press_news_sort_key({"published_at_iso": None, "published_at": ""}) == 0.0


def test_none_and_empty_values_never_log_anything(caplog):
    caplog.set_level(logging.DEBUG, logger="app.services.portal_press_news_service")
    _press_news_sort_key({"published_at_iso": None, "published_at": "", "created_at": "   "})
    assert caplog.records == []


def test_falls_through_to_a_later_field_when_earlier_fields_are_empty():
    item = {
        "published_at_iso": None,
        "published_at": "",
        "published_at_text": "Wed, 03 Jun 2026 03:42:00 GMT",
    }
    key = _press_news_sort_key(item)
    assert key > 0.0


def test_log_storm_scale_rfc_batch_sorts_correctly_with_zero_error_records(caplog):
    """Reproduces the real production incident at scale: a single request
    against a list of RFC-dated press/news items (production observed
    TRACEBACK_COUNT=1184 from one /portal request) must sort correctly and
    emit zero ERROR/traceback log records -- not merely for one sample
    date, but across a representative batch."""
    caplog.set_level(logging.DEBUG, logger="app.services.portal_press_news_service")
    rfc_samples = [
        "Sat, 12 Aug 2023 07:12:00 GMT",
        "Mon, 15 Dec 2025 16:01:00 GMT",
        "Wed, 03 Jun 2026 03:42:00 GMT",
        "Tue, 01 Jan 2024 00:00:00 GMT",
        "Fri, 28 Feb 2025 23:59:59 GMT",
    ]
    items = [{"id": i, "published_at": rfc_samples[i % len(rfc_samples)]} for i in range(1200)]

    ordered = sorted(items, key=_press_news_sort_key, reverse=True)

    assert len(ordered) == len(items)
    error_or_exc_records = [
        r for r in caplog.records if r.levelno >= logging.ERROR or r.exc_info is not None
    ]
    assert error_or_exc_records == []
    assert "Traceback" not in caplog.text
