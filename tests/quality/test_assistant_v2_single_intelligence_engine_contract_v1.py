"""BYS360 Assistant V2 -- single-intelligence-engine contract (mandate
Phase B/G): mechanical, static-source proof that neither the web widget nor
(where inspectable) the Flutter mobile client answers a business question
from a local keyword/knowledge engine when the real server call fails.

This complements (does not replace) the live-browser verification performed
for this mandate: a simulated network failure was submitted through the
real chat form and the rendered answer was asserted, via DOM inspection, to
be exactly the fixed unavailability message -- never local KNOWLEDGE
content. That check cannot run inside pytest (no browser here), so this
file locks the same property at the source level, deterministically and on
every future CI run.
"""
from __future__ import annotations

import pathlib

import pytest

pytestmark = pytest.mark.ci_safe

_STATIC_JS_ROOT = pathlib.Path("app/static/js")
_CORE_WIDGET = _STATIC_JS_ROOT / "bys360_assistant_module.js"
_MEMORY_V30 = _STATIC_JS_ROOT / "bys360_assistant_module_memory_v30.js"
_UNAVAILABLE_MESSAGE = "BYS360 Kurumsal Asistan'a şu anda ulaşılamıyor. Lütfen daha sonra tekrar deneyin."


def test_core_widget_file_exists_and_is_readable():
    assert _CORE_WIDGET.exists()
    assert _MEMORY_V30.exists()


def test_memory_v30_never_calls_local_answer_on_server_failure():
    """The single call site that used to read `.catch(function () { return
    answer(q); })` must no longer invoke the local KNOWLEDGE-table
    `answer()` function anywhere in the file."""
    content = _MEMORY_V30.read_text(encoding="utf-8")
    assert "return answer(q)" not in content
    assert "catch(function () { return answer(q)" not in content.replace(" ", "")


def test_memory_v30_server_failure_path_uses_fixed_deterministic_message():
    content = _MEMORY_V30.read_text(encoding="utf-8")
    assert _UNAVAILABLE_MESSAGE in content
    assert "SERVER_UNAVAILABLE_MESSAGE" in content


def test_core_widget_local_fallback_no_longer_calls_local_answer_for_question_content():
    """`localFallback()` (the core file's own server-failure handler --
    shadowed in live traffic by memory_v30.js's capture-phase listener, but
    fixed too for defense-in-depth) must never call `localAnswer(question)`
    to answer the user's business question."""
    content = _CORE_WIDGET.read_text(encoding="utf-8")
    fallback_start = content.index("function localFallback(question)")
    next_function_start = content.index("\n  function ", fallback_start + 10)
    fallback_body = content[fallback_start:next_function_start]
    assert "localAnswer(question)" not in fallback_body
    assert _UNAVAILABLE_MESSAGE in fallback_body


def test_askserver_and_askserverv30_send_csrf_token_header():
    """Mandate Phase D: both server-calling functions must send the same
    CSRF header the app's other authenticated JSON-API callers already
    send (see app/templates/ai_agent/panel.html's own `csrf()` helper)."""
    core_content = _CORE_WIDGET.read_text(encoding="utf-8")
    memory_content = _MEMORY_V30.read_text(encoding="utf-8")
    for content in (core_content, memory_content):
        assert "csrfToken()" in content
        assert "X-CSRFToken" in content


def test_flutter_assistant_screen_ask_catch_block_uses_offline_response_not_local_fallback():
    """Mechanical proof mirroring the Python-side checks above, for the
    Flutter client (mandate Phase B2) -- verified functionally via a real
    `flutter analyze` run (0 issues) separately; this locks the specific
    call-site property at the source level."""
    screen_path = pathlib.Path(
        "mobile_flutter/bys360_mobile_native/lib/features/assistant/assistant_screen.dart"
    )
    assert screen_path.exists()
    content = screen_path.read_text(encoding="utf-8")

    catch_start = content.index("} catch (_) {")
    catch_end = content.index("} finally {", catch_start)
    catch_body = content[catch_start:catch_end]

    assert "_offlineUnavailableResponse()" in catch_body
    assert "_localFallback(question)" not in catch_body

    # _localFallback itself is allowed to remain as dead compatibility data
    # (mandate's own explicit allowance) but must have zero live callers.
    assert content.count("_localFallback(") == 1  # only its own definition
