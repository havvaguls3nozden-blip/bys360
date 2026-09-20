"""BYS360 Assistant V2 -- anti-hallucination result contract (mandate Phase 9).

Every capability invocation returns exactly one `AssistantCapabilityResult`,
whose `status` is always one of the six `AssistantResultStatus` values below.
There is no seventh, implicit "make something up" path: a capability that
finds nothing returns `NO_DATA`, one that isn't authorized returns
`ACCESS_DENIED`, one that fails returns `SYSTEM_ERROR` -- never a fabricated
`DATA_FOUND` with invented content. `message` is always a short, safe,
user-facing string; it never echoes internal exception text, table names, or
other implementation details (see `capability_dispatcher.py` for where each
status is actually produced).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AssistantResultStatus(StrEnum):
    DATA_FOUND = "DATA_FOUND"
    NO_DATA = "NO_DATA"
    ACCESS_DENIED = "ACCESS_DENIED"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    AMBIGUOUS_REQUEST = "AMBIGUOUS_REQUEST"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    # Added for the safety-classifier / conversational-intent wave (mandate
    # Phase N): these three are produced BEFORE any capability is ever
    # dispatched -- OUT_OF_SCOPE and SENSITIVE_REQUEST come from
    # safety_classifier.py, CONVERSATIONAL_RESPONSE from
    # conversational_intents.py. None of the three ever carry `data`.
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    SENSITIVE_REQUEST = "SENSITIVE_REQUEST"
    CONVERSATIONAL_RESPONSE = "CONVERSATIONAL_RESPONSE"


@dataclass(frozen=True)
class AssistantCapabilityResult:
    status: AssistantResultStatus
    message: str
    capability_key: str | None = None
    module_key: str | None = None
    data: Any | None = None
    source_label: str | None = None
    candidates: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.status is AssistantResultStatus.DATA_FOUND


__all__ = ["AssistantResultStatus", "AssistantCapabilityResult"]
