"""BYS360 Portal video link -- host-allowlist and video-id validation negative tests.

Calls the real _portal_video_embed_url / _youtube_video_id functions
(app/portal/routes.py) directly -- no network calls, no HTTP round-trip, no
mocks. Proves that loose host matching (e.g. an .endswith("youtube.com")
style check that a lookalike host such as "notyoutube.com" would pass) is
rejected, and that no hostile payload ever leaks into a persisted embed URL.

_host_matches_domain (app/portal/routes.py) enforces exact-match-or-proper-
subdomain host checks, closing the lookalike-domain gap that a naive
.endswith() comparison would otherwise allow.
"""
from __future__ import annotations

from urllib.parse import urlparse

import pytest

DANGEROUS_SUBSTRINGS = ("<", ">", '"', "'", "javascript:", "data:")


def _embed_url(raw_url: str) -> str:
    from app.portal.routes import _portal_video_embed_url

    return _portal_video_embed_url(raw_url)


# ---------------------------------------------------------------------------
# 1) Scheme-level rejection: non-http(s) schemes never reach host/id parsing.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_url",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
    ],
)
def test_dangerous_scheme_is_rejected(raw_url: str) -> None:
    assert _embed_url(raw_url) == ""


# ---------------------------------------------------------------------------
# 2) Host-allowlist bypass attempts (lookalike / suffix / prefix spoofing).
# ---------------------------------------------------------------------------


def test_youtube_prefix_spoof_host_is_always_rejected() -> None:
    """'youtube.com.attacker.example' ends in 'attacker.example', so it never
    matched a naive .endswith("youtube.com") check either -- regression guard."""
    assert _embed_url("https://youtube.com.attacker.example/watch?v=dQw4w9WgXcQ") == ""


def test_vimeo_prefix_spoof_host_is_always_rejected() -> None:
    assert _embed_url("https://vimeo.com.attacker.example/12345") == ""


def test_notyoutube_lookalike_host_is_rejected() -> None:
    """"notyoutube.com".endswith("youtube.com") is True, so a naive suffix
    check would incorrectly accept this host. _host_matches_domain requires
    an exact match or a '.'-bounded subdomain, so this must be rejected."""
    assert _embed_url("https://notyoutube.com/watch?v=dQw4w9WgXcQ") == ""


def test_evil_youtube_lookalike_host_is_rejected() -> None:
    assert _embed_url("https://evil-youtube.com/watch?v=dQw4w9WgXcQ") == ""


def test_notavimeo_lookalike_host_is_rejected() -> None:
    """"notavimeo.com".endswith("vimeo.com") is True -- same class of bug as
    notyoutube.com above, verified against the Vimeo branch."""
    assert _embed_url("https://notavimeo.com/12345") == ""


def test_youtube_video_id_helper_rejects_lookalike_host_directly() -> None:
    """Unit-tests _youtube_video_id itself (not just the wrapping
    _portal_video_embed_url), since it has its own independent host gate."""
    from app.portal.routes import _youtube_video_id

    parsed = urlparse("https://notyoutube.com/watch?v=dQw4w9WgXcQ")
    assert _youtube_video_id(parsed) == ""


# ---------------------------------------------------------------------------
# 3) Malformed / hostile video-id payloads on an otherwise-legitimate host.
# ---------------------------------------------------------------------------


def test_quote_breaking_query_payload_is_rejected() -> None:
    """The 'v' query value contains '"><script>...' -- fails the strict
    [A-Za-z0-9_-]{6,32} id regex, so no embed URL (and no script markup) is
    ever produced."""
    raw = 'https://youtube.com/watch?v="><script>alert(1)</script>'
    assert _embed_url(raw) == ""


def test_too_short_video_id_is_rejected() -> None:
    assert _embed_url("https://youtube.com/watch?v=ab12") == ""


def test_too_long_video_id_is_rejected() -> None:
    over_long_id = "a" * 40
    assert _embed_url(f"https://youtube.com/watch?v={over_long_id}") == ""


def test_raw_iframe_markup_submitted_as_video_url_is_rejected() -> None:
    """A raw <iframe src="..."> string submitted as the video_url form value
    must simply fail scheme/host parsing (urlparse treats the leading '<' as
    an invalid scheme character, so parsed.scheme == "") -- it is never
    stored verbatim, never rendered as trusted HTML, and never produces an
    attachment."""
    raw = '<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>'
    assert _embed_url(raw) == ""


# ---------------------------------------------------------------------------
# 4) Blanket contract: no hostile input may ever leak dangerous characters
#    into the value that would become PortalPostAttachment.stored_path.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_url",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "https://youtube.com.attacker.example/watch?v=dQw4w9WgXcQ",
        "https://vimeo.com.attacker.example/12345",
        "https://notyoutube.com/watch?v=dQw4w9WgXcQ",
        "https://notavimeo.com/12345",
        'https://youtube.com/watch?v="><script>alert(1)</script>',
        "https://youtube.com/watch?v=ab12",
        f"https://youtube.com/watch?v={'a' * 40}",
        '<iframe src="https://www.youtube.com/embed/dQw4w9WgXcQ"></iframe>',
    ],
)
def test_no_hostile_input_ever_produces_a_stored_path_with_dangerous_substrings(raw_url: str) -> None:
    result = _embed_url(raw_url)
    for token in DANGEROUS_SUBSTRINGS:
        assert token not in result, (
            f"Input {raw_url!r} produced a result containing forbidden "
            f"substring {token!r}: {result!r}"
        )


# ---------------------------------------------------------------------------
# 5) Positive controls: legitimate hosts must still work (zero behavior
#    change for real YouTube/Vimeo links, including subdomains).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw_url", "expected"),
    [
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"),
        ("https://music.youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"),
        ("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ", "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"),
        ("https://vimeo.com/76979871", "https://player.vimeo.com/video/76979871"),
        ("https://www.vimeo.com/76979871", "https://player.vimeo.com/video/76979871"),
        ("https://player.vimeo.com/video/76979871", "https://player.vimeo.com/video/76979871"),
    ],
)
def test_legitimate_hosts_still_produce_the_expected_embed_url(raw_url: str, expected: str) -> None:
    assert _embed_url(raw_url) == expected
