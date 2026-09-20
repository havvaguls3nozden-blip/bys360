"""BYS360 Assistant V2 -- deterministic follow-up resolution (mandate Phase C).

Resolves a small, explicit set of Turkish referential phrases against the
SAFE structural references stored in the last conversation turn
(`conversation_context.ConversationTurn.entity_refs` -- id+label pairs only,
never full record payloads). This module never guesses: if a referential
phrase is detected but there is no usable prior turn, or the reference could
mean more than one thing, it reports `ambiguous=True` and the caller
(`service.py`) must surface `AMBIGUOUS_REQUEST`, never pick a candidate on
its own.

Re-authorization note: resolving "İlkini göster" to a specific entity id
does NOT mean that entity's data gets reused from conversation state --
`service.py` takes the resolved id and makes a fresh
`capability_dispatcher.invoke_capability()` call for the CURRENT request's
authenticated user, exactly like any other capability invocation. This
module only ever returns which capability/entity a phrase refers to, never
any actual data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.assistant_v2.conversation_context import ConversationState

_REFERENTIAL_MARKERS = (
    "onlardan", "onlarn", "bunlardan", "ilkini", "ilk", "bu kişi", "bu kisi",
    "bu dönemdeki", "bu donemdeki", "bir önceki", "bir onceki", "önceki",
    "onceki", "bunu", "onu", "şunu", "sunu",
)


@dataclass(frozen=True)
class FollowUpResolution:
    is_follow_up: bool
    capability_key: str | None = None
    resolved_entity_id: Any | None = None
    ambiguous: bool = False
    ambiguous_reason: str | None = None


def looks_like_follow_up(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in _REFERENTIAL_MARKERS)


def resolve_follow_up(text: str, state: ConversationState | None) -> FollowUpResolution:
    """Returns `is_follow_up=False` immediately if `text` contains no
    referential marker at all -- the caller should then treat this as a
    fresh, independent question via the normal intent router, not a
    follow-up."""
    if not looks_like_follow_up(text):
        return FollowUpResolution(is_follow_up=False)

    last_turn = state.last_turn if state else None
    if last_turn is None or not last_turn.entity_refs:
        # "İlkini göster" (or any other referential phrase) with no previous
        # bounded list to refer back to -- the mandate's own explicit
        # example of what must become AMBIGUOUS_REQUEST, never a guess.
        return FollowUpResolution(is_follow_up=True, ambiguous=True, ambiguous_reason="no_previous_bounded_list")

    lowered = text.lower()

    if "ilk" in lowered:
        return FollowUpResolution(
            is_follow_up=True,
            capability_key=last_turn.capability_key,
            resolved_entity_id=last_turn.entity_refs[0].id,
        )

    if "bu kişi" in lowered or "bu kisi" in lowered:
        if len(last_turn.entity_refs) == 1:
            return FollowUpResolution(
                is_follow_up=True,
                capability_key=last_turn.capability_key,
                resolved_entity_id=last_turn.entity_refs[0].id,
            )
        # "Bu kişi" with two (or more) possible people from the last turn --
        # the mandate's own explicit second example of a required
        # AMBIGUOUS_REQUEST.
        return FollowUpResolution(
            is_follow_up=True,
            capability_key=last_turn.capability_key,
            ambiguous=True,
            ambiguous_reason="multiple_candidates",
        )

    # A generic follow-up about "the same topic" ("onlardan hangileri...",
    # "bu dönemdekileri özetle", "bir önceki birime göre") without a single
    # resolvable entity: re-run the SAME capability fresh (never the stored
    # data) so the caller gets a current, re-authorized answer about the
    # same subject rather than a guessed specific record.
    return FollowUpResolution(is_follow_up=True, capability_key=last_turn.capability_key)


__all__ = ["FollowUpResolution", "looks_like_follow_up", "resolve_follow_up"]
