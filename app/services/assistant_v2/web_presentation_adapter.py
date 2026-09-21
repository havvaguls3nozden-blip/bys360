"""BYS360 Assistant V2 -- web presentation adapter (mandate Phase E).

Maps an `AssistantAnswer` (the full V2 API contract) down to the minimal
shape the EXISTING, already-shipped web assistant UI actually reads --
`app/static/js/bys360_assistant_module.js`'s `askServer()` reads only
`payload.answer` (falling back to `.reply`/`.message`) and
`payload.actions` (falling back to `.suggestions`), and
`app/templates/ai_agent/panel.html`'s `ask()` reads only `data.answer` and
`data.actions` (falling back to `.suggested_actions`). Both already render
an action item from any of `.url`/`.route`/`.href` and `.label`/`.title`, so
no JS change is needed -- `related_links`'s existing `{"label", "url"}`
shape (Phase D) already matches both readers.

No business logic lives here: this is a pure, stateless field-mapping
function over an already-computed `AssistantAnswer` -- it never calls
`AssistantV2Service` itself and never makes an authorization decision.
"""
from __future__ import annotations

from typing import Any

from app.services.assistant_v2.capability_registry import resolve_suggestion_label
from app.services.settings.module_registry import get_module


def _module_label(module_keys: tuple[str, ...]) -> str | None:
    if not module_keys:
        return None
    module = get_module(module_keys[0])
    return module.display_name if module else None


def adapt_for_legacy_web(answer: Any) -> dict[str, Any]:
    """`answer` is an `AssistantV2Service.AssistantAnswer`. Returns the
    legacy-widget-compatible JSON body. `answer`/`actions` are the two
    fields the existing JS has always read (unchanged, still the only two
    fields required for the widget to keep working exactly as before).
    `sources`/`module`/`suggested_questions` are new, purely ADDITIVE
    fields (mandate Phase L: provenance chips, module badge, clarification
    suggestions) -- an older cached copy of the JS simply ignores them, so
    adding them here can never break the existing widget."""
    suggested_questions: list[str] = []
    if answer.clarification and isinstance(answer.clarification.get("candidates"), list):
        # Never the raw capability_key (an internal identifier, e.g.
        # "file_center_read_quota_status") -- resolve_suggestion_label()
        # always returns a human-readable Turkish phrase instead.
        suggested_questions = [resolve_suggestion_label(str(c)) for c in answer.clarification["candidates"]]

    return {
        "answer": answer.answer,
        "actions": list(answer.related_links),
        "sources": [{"label": s.label, "url": s.url} for s in answer.sources],
        "module": _module_label(answer.module_keys),
        "suggested_questions": suggested_questions,
        # Phase B (conversation_id web integration): additive field -- the
        # widget stores this and resends it on the next question so
        # AssistantV2Service can resolve a genuine follow-up. Omitting it
        # (an older cached JS copy) only means the widget never gets
        # multi-turn continuity, never a broken response -- AssistantV2Service.ask()
        # already treats a missing conversation_id as "start fresh" (see
        # its own docstring).
        "conversation_id": answer.conversation_id,
    }


__all__ = ["adapt_for_legacy_web"]
