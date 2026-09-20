"""BYS360 Assistant V2 -- mobile presentation adapter (mandate Phase H).

Maps an `AssistantAnswer` (the V2 API contract) to the exact JSON shape the
LIVE Flutter `AssistantScreen` already parses (confirmed by direct source
read of `mobile_flutter/bys360_mobile_native/lib/features/assistant/assistant_screen.dart`):
`answer, module, route_hint, required_roles, steps, warnings, control_items,
suggested_questions, intent`. Every field is derived only from data V2
already computed and authorized -- nothing here invents a route, a role
list, or a step that wasn't already produced by a real capability/guide
(Phase H's explicit "no fake required_roles" / "no arbitrary generated
navigation" rules):

  - `module`      -- the target module's real `display_name` from
                      `app.services.settings.module_registry` (never a raw
                      key, never invented text).
  - `route_hint`  -- only ever the URL from `answer.related_links[0]`,
                      itself already re-authorized for the current user by
                      `AssistantV2Service` (Phase D/I) -- never a
                      client-guessed or unauthorized path.
  - `required_roles` -- mechanically derived from the REAL
                      `app.menu_registry.get_role_default_menu_keys` for
                      every role in `app.admin.routes.ROLE_CHOICES` (the
                      app's own canonical role list), not a hand-typed
                      guess. Empty when the answer carries no
                      `capability_key` (e.g. a conversational reply) or the
                      capability's permission_key can't be resolved.
  - `steps` / `warnings` -- only ever populated from a procedural guide's
                      OWN registered `steps`/`warnings` (never synthesized
                      for a plain data-capability answer, since those have
                      no step content to report -- Phase H: never fabricate).
  - `control_items` -- no V2-native equivalent exists yet (the legacy field
                      was a bespoke verification checklist authored per
                      topic) -- always an empty list rather than invented
                      content; a future wave could add this to
                      `ProceduralGuideEntry` if the product wants it.
  - `suggested_questions` -- only from `clarification.candidates` on an
                      AMBIGUOUS_REQUEST (real routing candidates, not
                      generated text) -- empty otherwise.
  - `intent`      -- a small, fully deterministic mapping from
                      `status`/`capability_key`, documented in
                      `_INTENT_FOR_STATUS` below -- never free text.
"""
from __future__ import annotations

from typing import Any

from app.admin.routes import ROLE_CHOICES
from app.menu_registry import get_role_default_menu_keys
from app.services.assistant_v2.capability_registry import get_capability
from app.services.assistant_v2.procedural_guides import get_guide
from app.services.settings.module_registry import get_module

_INTENT_FOR_STATUS: dict[str, str] = {
    "ACCESS_DENIED": "ACCESS_DENIED",
    "NO_DATA": "NO_DATA",
    "CAPABILITY_UNAVAILABLE": "CAPABILITY_UNAVAILABLE",
    "AMBIGUOUS_REQUEST": "AMBIGUOUS_REQUEST",
    "SYSTEM_ERROR": "SYSTEM_ERROR",
    "OUT_OF_SCOPE": "OUT_OF_SCOPE",
    "SENSITIVE_REQUEST": "SENSITIVE_REQUEST",
    "CONVERSATIONAL_RESPONSE": "CONVERSATIONAL",
}


def _module_display_name(module_keys: tuple[str, ...]) -> str:
    if not module_keys:
        return "BYS360 Asistanı"
    module = get_module(module_keys[0])
    return module.display_name if module else "BYS360 Asistanı"


def _route_hint(related_links: tuple[dict[str, str], ...]) -> str:
    if not related_links:
        return ""
    return related_links[0].get("url", "") or ""


def _required_roles(capability_key: str | None) -> list[str]:
    if not capability_key:
        return []
    entry = get_capability(capability_key)
    permission_key = entry.permission_key if entry else None
    if permission_key is None:
        guide = get_guide(capability_key)
        permission_key = guide.required_permission if guide else None
    if not permission_key:
        return []
    return [role for role, _label in ROLE_CHOICES if permission_key in get_role_default_menu_keys(role)]


def _guide_steps_and_warnings(capability_key: str | None) -> tuple[list[str], list[str]]:
    if not capability_key:
        return [], []
    guide = get_guide(capability_key)
    if guide is None:
        return [], []
    return list(guide.steps), list(guide.warnings)


def _intent_for(status: str, capability_key: str | None) -> str:
    # A guide's own key survives onto a denied/unavailable result too (it
    # identifies WHICH guide was requested, not that it was served) -- so
    # the DATA_FOUND check must come first, otherwise an ACCESS_DENIED
    # guide lookup would be mis-reported as a successful PROCEDURAL_GUIDE
    # answer.
    if status == "DATA_FOUND" and capability_key and get_guide(capability_key) is not None:
        return "PROCEDURAL_GUIDE"
    return _INTENT_FOR_STATUS.get(status, status)


def adapt_for_mobile(answer: Any) -> dict[str, Any]:
    """`answer` is an `AssistantV2Service.AssistantAnswer`. Returns the
    Flutter-compatible JSON body."""
    steps, warnings = _guide_steps_and_warnings(answer.capability_key)
    suggested_questions: list[str] = []
    if answer.clarification and isinstance(answer.clarification.get("candidates"), list):
        suggested_questions = [str(c) for c in answer.clarification["candidates"]]

    return {
        "answer": answer.answer,
        "module": _module_display_name(answer.module_keys),
        "route_hint": _route_hint(answer.related_links),
        "required_roles": _required_roles(answer.capability_key),
        "steps": steps,
        "warnings": warnings,
        "control_items": [],
        "suggested_questions": suggested_questions,
        "intent": _intent_for(answer.status, answer.capability_key),
    }


__all__ = ["adapt_for_mobile"]
