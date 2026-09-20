"""BYS360 Assistant V2 -- deterministic intent routing with confidence
(mandate Phase 5, confidence model, domain vocabulary integration).

"Intent routing must not grant access. Routing determines candidate
capabilities only. Authorization happens separately." This module does
exactly that: given free-text user input, it scores every active
capability's `intent_tags` against the query's token set (widened with
`domain_vocabulary.expand_query_tokens` -- synonyms + a light, conservative
suffix strip, never a real stemmer), and returns a `ConfidenceTier` alongside
the ranked candidates:

  HIGH   -- one capability clearly outscores every other; safe to execute
            directly.
  MEDIUM -- multiple capabilities are close in score; the caller must ask
            for clarification, never silently pick one.
  LOW    -- nothing scored above zero; the caller must treat this as
            AMBIGUOUS_REQUEST / CAPABILITY_UNAVAILABLE, never guess.

This module never touches the database, never checks who the user is, and
never decides whether anything is allowed -- that is
`capability_dispatcher.invoke_capability`'s job, called separately and only
after a candidate is chosen. No LLM, no fuzzy/semantic matching, no
model-generated queries -- every match is explainable by re-reading this
file (mandate Phase 5/7: deterministic routing, no raw SQL/ORM generation
from natural language).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.services.assistant_v2.capability_registry import (
    AssistantCapabilityEntry,
    list_active_capabilities,
)
from app.services.assistant_v2.domain_vocabulary import expand_query_tokens

# A candidate is considered part of a "close competition" (-> MEDIUM) when
# its score is within this fraction of the top score. Deliberately a
# constant, not tunable per call, so the confidence boundary stays
# consistent and testable across the whole assistant.
_MEDIUM_CONFIDENCE_RATIO = 0.75


class ConfidenceTier(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class ScoredCapability:
    capability_key: str
    module_key: str
    score: int


@dataclass(frozen=True)
class IntentResolution:
    tier: ConfidenceTier
    candidates: tuple[ScoredCapability, ...]

    @property
    def best_capability_key(self) -> str | None:
        return self.candidates[0].capability_key if self.candidates else None


def _score_capability(query_tokens: set[str], entry: AssistantCapabilityEntry) -> int:
    """Counts how many of the (vocabulary-expanded) query tokens appear
    inside this capability's intent_tags. A multi-word tag naturally scores
    higher than a single-word one when more of its words are present."""
    if not query_tokens:
        return 0
    score = 0
    for tag in entry.intent_tags:
        tag_tokens = expand_query_tokens(tag)
        score += len(query_tokens & tag_tokens)
    return score


def _rank(query_tokens: set[str], *, module_key: str | None) -> list[ScoredCapability]:
    scored: list[tuple[int, int, ScoredCapability]] = []
    for index, entry in enumerate(list_active_capabilities()):
        if module_key is not None and entry.module_key != module_key:
            continue
        score = _score_capability(query_tokens, entry)
        if score > 0:
            scored.append((score, index, ScoredCapability(entry.capability_key, entry.module_key, score)))
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [row[2] for row in scored]


def resolve_intent(text: str, *, max_candidates: int = 5, module_key: str | None = None) -> IntentResolution:
    """The confidence-aware entry point. Always returns an
    `IntentResolution`; an empty `candidates` tuple with tier=LOW means
    "nothing matched, do not guess"."""
    query_tokens = expand_query_tokens(text)
    ranked = _rank(query_tokens, module_key=module_key)[:max_candidates]

    if not ranked:
        return IntentResolution(tier=ConfidenceTier.LOW, candidates=())

    top_score = ranked[0].score
    close_competitors = [c for c in ranked if c.score >= top_score * _MEDIUM_CONFIDENCE_RATIO]

    if len(close_competitors) == 1:
        return IntentResolution(tier=ConfidenceTier.HIGH, candidates=tuple(ranked))
    return IntentResolution(tier=ConfidenceTier.MEDIUM, candidates=tuple(close_competitors))


def resolve_intent_candidates(
    text: str,
    *,
    max_candidates: int = 5,
    module_key: str | None = None,
) -> list[str]:
    """Backward-compatible plain candidate list (used by callers that don't
    need the confidence tier), kept so existing tests/call sites written
    before the confidence model do not need to change their shape."""
    return [c.capability_key for c in resolve_intent(text, max_candidates=max_candidates, module_key=module_key).candidates]


def resolve_module_candidates(text: str, *, max_candidates: int = 3) -> list[str]:
    """Coarser variant of the same scoring, aggregated to module_key instead
    of capability_key -- useful for an initial "which module is this about"
    step before narrowing to a specific capability."""
    query_tokens = expand_query_tokens(text)
    if not query_tokens:
        return []
    totals: dict[str, int] = {}
    first_seen_order: dict[str, int] = {}
    for index, entry in enumerate(list_active_capabilities()):
        score = _score_capability(query_tokens, entry)
        if score <= 0:
            continue
        totals[entry.module_key] = totals.get(entry.module_key, 0) + score
        first_seen_order.setdefault(entry.module_key, index)
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], first_seen_order[kv[0]]))
    return [module_key for module_key, _total in ranked[:max_candidates]]


__all__ = [
    "ConfidenceTier",
    "ScoredCapability",
    "IntentResolution",
    "resolve_intent",
    "resolve_intent_candidates",
    "resolve_module_candidates",
]
