"""BYS360 Assistant V2 -- deterministic intent routing for procedural guides
(mandate Phase C). Mirrors `intent_router.py`'s scoring approach exactly
(same vocabulary expansion, same confidence-tier shape) but scores against
`procedural_guides.PROCEDURAL_GUIDE_REGISTRY` instead of the data-capability
registry, kept as a small, separate module so guide routing can never
accidentally influence or be influenced by data-capability routing scores.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.assistant_v2.domain_vocabulary import expand_query_tokens
from app.services.assistant_v2.intent_router import ConfidenceTier
from app.services.assistant_v2.procedural_guides import ProceduralGuideEntry, list_active_guides

_MEDIUM_CONFIDENCE_RATIO = 0.75

# A bare, topic-less procedural marker (e.g. just "nasıl kullanılır" with no
# actual subject) can score a low, non-zero overlap against some guide's
# intent_tags purely by vocabulary-expansion noise (observed: score 1 via
# domain_vocabulary's synonym expansion), which is NOT a genuine topic
# match -- every real topic match observed scores >= 4 (see
# test_assistant_v2_procedural_guides_contract_v1.py). Filtering below this
# floor keeps a generic "how do I use this app" question from being
# mis-answered as a specific, unrelated guide.
_MIN_ABSOLUTE_SCORE = 3

# A bare topic noun (e.g. "personel") appears in several guides' intent_tags
# at once (personel ekle / personel kaydı / ...), so scoring alone cannot
# reliably tell a procedural "how do I add personnel" question apart from a
# plain data query like "personel listele" -- both share the word "personel".
# Real procedural questions in Turkish reliably carry an explicit "how"
# marker the data-query phrasing never uses; requiring one before scoring at
# all keeps guide routing from ever intercepting a genuine data-capability
# query (mirrors how the legacy assistant_step_guide.py itself only matched
# on full multi-word phrases, never a bare topic noun).
_PROCEDURAL_MARKERS = ("nasil", "nasıl", "adim", "adım", "ne yapmaliyim", "ne yapmalıyım", "hangi adim", "hangi adım")


def _looks_procedural(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in _PROCEDURAL_MARKERS)


@dataclass(frozen=True)
class ScoredGuide:
    guide_key: str
    module_key: str
    score: int


@dataclass(frozen=True)
class GuideResolution:
    tier: ConfidenceTier
    candidates: tuple[ScoredGuide, ...]

    @property
    def best_guide_key(self) -> str | None:
        return self.candidates[0].guide_key if self.candidates else None


def _score_guide(query_tokens: set[str], entry: ProceduralGuideEntry) -> int:
    if not query_tokens:
        return 0
    score = 0
    for tag in entry.intent_tags:
        tag_tokens = expand_query_tokens(tag)
        score += len(query_tokens & tag_tokens)
    return score


def resolve_guide_intent(text: str, *, max_candidates: int = 5) -> GuideResolution:
    if not _looks_procedural(text):
        return GuideResolution(tier=ConfidenceTier.LOW, candidates=())
    query_tokens = expand_query_tokens(text)
    scored: list[tuple[int, int, ScoredGuide]] = []
    for index, entry in enumerate(list_active_guides()):
        score = _score_guide(query_tokens, entry)
        if score >= _MIN_ABSOLUTE_SCORE:
            scored.append((score, index, ScoredGuide(entry.guide_key, entry.module_key, score)))
    scored.sort(key=lambda row: (-row[0], row[1]))
    ranked = [row[2] for row in scored[:max_candidates]]

    if not ranked:
        return GuideResolution(tier=ConfidenceTier.LOW, candidates=())

    top_score = ranked[0].score
    close_competitors = [c for c in ranked if c.score >= top_score * _MEDIUM_CONFIDENCE_RATIO]

    if len(close_competitors) == 1:
        return GuideResolution(tier=ConfidenceTier.HIGH, candidates=tuple(ranked))
    return GuideResolution(tier=ConfidenceTier.MEDIUM, candidates=tuple(close_competitors))


__all__ = ["ScoredGuide", "GuideResolution", "resolve_guide_intent"]
