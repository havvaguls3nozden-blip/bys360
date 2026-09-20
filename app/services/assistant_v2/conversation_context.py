"""BYS360 Assistant V2 -- safe conversation context (mandate Phase A/B).

Storage decision (explicit, not silent): conversation state lives in the
Flask session (server-signed, already-existing infrastructure tied to the
authenticated user via Flask-Login) -- NOT a new database table. This is
"prefer existing persistence if suitable" applied literally: the mandate's
own Phase A explicitly requires stopping before any migration, and nothing
stored here needs to survive a browser session or be queryable outside it,
so no schema change is needed at all. If a future requirement needs
cross-device conversation history, THAT would be the point to stop and
propose a real migration -- not this wave.

What is stored per turn (and nothing else): `capability_key`, `module_key`,
a small bounded list of `entity_refs` (id + short label pairs, e.g. from
the last LIST-shaped result -- never full record payloads), a
`safe_summary` string capped at `MAX_SAFE_SUMMARY_CHARS`, `source_labels`,
and a timestamp. No personnel/performance field values beyond what was
already a public-safe label are ever persisted here.

Re-authorization (Phase B): this module NEVER re-serves data from a stored
turn. `get_conversation_state()` returns only structural references (which
capability, which entity IDs were mentioned); resolving a follow-up always
means calling `capability_dispatcher.invoke_capability()` again, fresh, for
the current request's `current_user` -- see `service.py`. A conversation
whose stored `user_id` does not match the live authenticated user's id is
treated as foreign and never used (covers session/user substitution and a
crafted/reused conversation_id belonging to someone else).
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from flask import session

from app.services.assistant_v2.limits import (
    MAX_CONVERSATION_TURNS_RETAINED,
    MAX_ENTITY_REFS_PER_TURN,
    MAX_SAFE_SUMMARY_CHARS,
    MAX_SOURCE_COUNT,
)

_SESSION_KEY = "bys360_assistant_v2_conversation"


@dataclass(frozen=True)
class EntityRef:
    id: Any
    label: str


@dataclass(frozen=True)
class ConversationTurn:
    capability_key: str | None
    module_key: str | None
    entity_refs: tuple[EntityRef, ...]
    safe_summary: str
    source_labels: tuple[str, ...]
    timestamp: str


@dataclass(frozen=True)
class ConversationState:
    conversation_id: str
    user_id: int
    turns: tuple[ConversationTurn, ...] = field(default_factory=tuple)

    @property
    def last_turn(self) -> ConversationTurn | None:
        return self.turns[-1] if self.turns else None


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _clip_summary(text: str) -> str:
    text = (text or "").strip()
    if len(text) <= MAX_SAFE_SUMMARY_CHARS:
        return text
    return text[: MAX_SAFE_SUMMARY_CHARS - 1].rstrip() + "…"


def start_new_conversation(user: Any) -> str:
    """Generates a fresh conversation_id and clears any prior state for this
    user's session -- always used when a caller cannot resolve/trust an
    existing conversation_id (unknown id, foreign user, or none supplied)."""
    conversation_id = uuid.uuid4().hex
    user_id = getattr(user, "id", None)
    session[_SESSION_KEY] = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "turns": [],
    }
    return conversation_id


def get_conversation_state(user: Any, conversation_id: str | None) -> ConversationState | None:
    """Returns the stored state ONLY if a conversation_id was supplied, a
    session record exists, its conversation_id matches, AND its stored
    user_id matches the live authenticated user. Any mismatch (foreign
    conversation_id, session user substitution, no session) returns None --
    the caller must then start a new conversation, never fall back to
    guessing whose state it might be."""
    if not conversation_id:
        return None
    raw = session.get(_SESSION_KEY)
    if not isinstance(raw, dict):
        return None
    if raw.get("conversation_id") != conversation_id:
        return None
    user_id = getattr(user, "id", None)
    if user_id is None or raw.get("user_id") != user_id:
        return None
    turns = tuple(
        ConversationTurn(
            capability_key=t.get("capability_key"),
            module_key=t.get("module_key"),
            entity_refs=tuple(EntityRef(id=r.get("id"), label=r.get("label", "")) for r in t.get("entity_refs", [])),
            safe_summary=t.get("safe_summary", ""),
            source_labels=tuple(t.get("source_labels", ())),
            timestamp=t.get("timestamp", ""),
        )
        for t in raw.get("turns", [])
    )
    return ConversationState(conversation_id=conversation_id, user_id=user_id, turns=turns)


def record_turn(
    user: Any,
    conversation_id: str,
    *,
    capability_key: str | None,
    module_key: str | None,
    entity_refs: list[tuple[Any, str]],
    safe_summary: str,
    source_labels: list[str],
) -> None:
    """Appends one bounded turn to the session-stored conversation. Only
    ever called for the current, live, authenticated user -- there is no
    code path that writes a turn on behalf of a different user_id."""
    user_id = getattr(user, "id", None)
    raw = session.get(_SESSION_KEY)
    if not isinstance(raw, dict) or raw.get("conversation_id") != conversation_id or raw.get("user_id") != user_id:
        raw = {"conversation_id": conversation_id, "user_id": user_id, "turns": []}

    turn = {
        "capability_key": capability_key,
        "module_key": module_key,
        "entity_refs": [{"id": ref_id, "label": str(label)[:120]} for ref_id, label in entity_refs[:MAX_ENTITY_REFS_PER_TURN]],
        "safe_summary": _clip_summary(safe_summary),
        "source_labels": list(source_labels[:MAX_SOURCE_COUNT]),
        "timestamp": _now_iso(),
    }
    turns = raw.get("turns", [])
    turns.append(turn)
    raw["turns"] = turns[-MAX_CONVERSATION_TURNS_RETAINED:]
    session[_SESSION_KEY] = raw


def clear_conversation(user: Any) -> None:
    session.pop(_SESSION_KEY, None)


def conversation_state_as_dict(state: ConversationState) -> dict[str, Any]:
    """Debug/test convenience -- never includes anything beyond what is
    already in ConversationState (i.e. never a raw record payload)."""
    return asdict(state)


__all__ = [
    "EntityRef",
    "ConversationTurn",
    "ConversationState",
    "start_new_conversation",
    "get_conversation_state",
    "record_turn",
    "clear_conversation",
    "conversation_state_as_dict",
]
