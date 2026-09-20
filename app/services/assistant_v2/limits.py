"""BYS360 Assistant V2 -- named limit constants (mandate Phase N).

Every bound the assistant enforces lives here, as a named constant, so
nothing is a magic number scattered across modules. Callers that truncate
anything against one of these limits must say so in the response (see
`service.py`'s `truncated` handling) -- a silent truncation is treated the
same as a silent hallucination by this project's own standards.
"""
from __future__ import annotations

MAX_CONVERSATION_TURNS_RETAINED = 5
MAX_SAFE_SUMMARY_CHARS = 240
MAX_ENTITY_REFS_PER_TURN = 20
MAX_SOURCE_COUNT = 5
MAX_QUERY_LENGTH = 500
MAX_ANSWER_LENGTH = 4000
MAX_LIST_ITEMS_RENDERED = 8

__all__ = [
    "MAX_CONVERSATION_TURNS_RETAINED",
    "MAX_SAFE_SUMMARY_CHARS",
    "MAX_ENTITY_REFS_PER_TURN",
    "MAX_SOURCE_COUNT",
    "MAX_QUERY_LENGTH",
    "MAX_ANSWER_LENGTH",
    "MAX_LIST_ITEMS_RENDERED",
]
