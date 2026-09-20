"""BYS360 Assistant V2 -- the ONE application service entry point (mandate
Phase D / L).

    Web/API Route
        -> AssistantV2Service.ask()
            -> intent_router / follow_up_resolver   (routing only, no access)
            -> capability_dispatcher.invoke_capability()   (THE auth gate, re-run every call)
            -> response_composer                     (native Turkish rendering)
            -> source-link authorization (Phase I)
            -> conversation_context.record_turn()
        -> AssistantAnswer (the stable API contract, Phase L)

No business intelligence lives in the Flask route -- `ask()` is the only
thing a route ever calls. Every follow-up re-runs `invoke_capability()`
fresh for the CURRENT authenticated user (Phase B): a resolved follow-up
reference is never served from conversation-stored data, only used to
re-query and then narrow a brand-new, freshly-authorized result.
"""
from __future__ import annotations

import importlib
import inspect
import logging
from dataclasses import dataclass
from typing import Any

from app.route_support import can_access_menu
from app.services.assistant_v2.capability_dispatcher import invoke_capability
from app.services.assistant_v2.capability_registry import get_capability
from app.services.assistant_v2.conversation_context import (
    get_conversation_state,
    record_turn,
    start_new_conversation,
)
from app.services.assistant_v2.conversational_intents import (
    ConversationalIntent,
    detect as detect_conversational,
)
from app.services.assistant_v2.cross_module_orchestrator import personnel_pending_evaluation_in_unit
from app.services.assistant_v2.follow_up_resolver import resolve_follow_up
from app.services.assistant_v2.guide_dispatcher import invoke_guide
from app.services.assistant_v2.guide_intent_router import resolve_guide_intent
from app.services.assistant_v2.intent_router import ConfidenceTier, resolve_intent
from app.services.assistant_v2.limits import MAX_QUERY_LENGTH, MAX_SOURCE_COUNT
from app.services.assistant_v2.page_context import explain_page, resolve_page_context
from app.services.assistant_v2.procedural_guides import get_guide
from app.services.assistant_v2.related_links import resolve_related_link
from app.services.assistant_v2.response_composer import (
    compose_cross_module_response,
    compose_guide_response,
    compose_response,
)
from app.services.assistant_v2.result_contract import (
    AssistantCapabilityResult,
    AssistantResultStatus,
)
from app.services.assistant_v2.safety_classifier import SafetyCategory, classify as classify_safety

logger = logging.getLogger(__name__)

_ID_LIKE_KEYS = ("id", "sicil_no", "employee_id")


@dataclass(frozen=True)
class SourceCard:
    label: str
    url: str | None  # None means "label only, not clickable" (Phase I)


@dataclass(frozen=True)
class AssistantAnswer:
    status: str
    answer: str
    capability_key: str | None
    module_keys: tuple[str, ...]
    sources: tuple[SourceCard, ...]
    conversation_id: str
    clarification: dict[str, Any] | None
    related_links: tuple[dict[str, str], ...]


def _clip_query(text: str) -> str:
    text = (text or "").strip()
    return text[:MAX_QUERY_LENGTH]


def _extract_id(row: Any) -> Any:
    if isinstance(row, dict):
        for key in _ID_LIKE_KEYS:
            if row.get(key) is not None:
                return row[key]
    return None


def _extract_label(row: Any) -> str:
    if isinstance(row, dict):
        for key in ("full_name", "title", "display_name", "sicil_no", "name"):
            if row.get(key):
                return str(row[key])
    return str(row)


def _entity_refs_from_data(data: Any) -> list[tuple[Any, str]]:
    if not isinstance(data, list):
        return []
    refs = []
    for row in data:
        entity_id = _extract_id(row)
        if entity_id is not None:
            refs.append((entity_id, _extract_label(row)))
    return refs


def _safe_source_url(user: Any, permission_key: str | None, url: str | None) -> str | None:
    """Phase I: a source card may only be clickable if the CURRENT user can
    access the target screen's own menu key -- re-checked here, not assumed
    from the capability having already been authorized (the target page may
    be a different menu key than the capability itself, e.g. a Settings
    Center page)."""
    if not url:
        return None
    if permission_key is None:
        return url  # self-describing / auth_override capabilities have no single menu_key to re-check
    try:
        if can_access_menu(user, permission_key):
            return url
    except Exception:
        logger.exception("assistant_v2 service: source-link authorization re-check failed for permission_key=%s", permission_key)
    return None


def _build_sources(user: Any, result: AssistantCapabilityResult) -> tuple[SourceCard, ...]:
    if not result.source_label:
        return ()
    entry = get_capability(result.capability_key) if result.capability_key else None
    permission_key = entry.permission_key if entry else None
    url = _safe_source_url(user, permission_key, None)
    return (SourceCard(label=result.source_label, url=url),)[:MAX_SOURCE_COUNT]


def _build_related_links_for_capability(user: Any, result: AssistantCapabilityResult) -> tuple[dict[str, str], ...]:
    """Phase D: a related "go to this screen" action button, derived only
    from a trusted server-side registry (never a client- or LLM-supplied
    URL) and re-authorized for the CURRENT user before being returned."""
    if result.status is not AssistantResultStatus.DATA_FOUND or not result.capability_key:
        return ()
    entry = get_capability(result.capability_key)
    if entry is None or not entry.permission_key:
        return ()
    link = resolve_related_link(user, entry.permission_key, f"{entry.display_name} ekranına git")
    return (link,) if link else ()


def _build_related_links_for_guide(user: Any, result: AssistantCapabilityResult) -> tuple[dict[str, str], ...]:
    if result.status is not AssistantResultStatus.DATA_FOUND or not result.capability_key:
        return ()
    entry = get_guide(result.capability_key)
    if entry is None or not entry.required_permission:
        return ()
    link = resolve_related_link(user, entry.required_permission, f"{entry.title} ekranına git")
    return (link,) if link else ()


def _extra_kwargs_for(capability_key: str, query: str) -> dict[str, Any]:
    """A small, explicit, registry-driven mechanism for the rare capability
    that needs the user's own free-text question as a parameter (currently
    only virtual_assistant_search_knowledge_bank, via its
    extra={"question_kwarg": "question"}) -- never a guessed/invented
    value, always the exact text the user typed, already length-bounded by
    _clip_query()."""
    entry = get_capability(capability_key)
    if entry is None or not entry.extra:
        return {}
    kwarg_name = entry.extra.get("question_kwarg")
    if kwarg_name:
        return {kwarg_name: query}
    return {}


def _capability_needs_unavailable_parameters(capability_key: str, *, available_kwargs: set[str] | None = None) -> bool:
    """True if the capability's real handler requires a positional/keyword
    argument beyond `user` (and beyond whatever's already in
    `available_kwargs`, e.g. from _extra_kwargs_for) that this service has
    no value for (e.g. personnel_hr_read_personnel_record needs a
    sicil_no). Checked via real signature inspection, not a hand-maintained
    list, so a new parameterized capability is automatically covered
    without needing this function updated. Prevents attempting a call that
    would fail with a TypeError -- which capability_dispatcher would
    correctly catch and turn into SYSTEM_ERROR, but silently guessing or
    crashing into an error is worse than admitting up front that more
    information is needed."""
    available_kwargs = available_kwargs or set()
    entry = get_capability(capability_key)
    if entry is None:
        return False
    try:
        module_path, _, attr_name = entry.service_handler.rpartition(".")
        handler = getattr(importlib.import_module(module_path), attr_name)
        signature = inspect.signature(handler)
    except Exception:
        logger.exception("assistant_v2 service: could not inspect handler signature for capability_key=%s", capability_key)
        return True  # fail closed: if we can't tell, don't guess
    params = list(signature.parameters.values())[1:]  # skip `user`
    for param in params:
        if (
            param.default is inspect.Parameter.empty
            and param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
            and param.name not in available_kwargs
        ):
            return True
    return False


_PAGE_HELP_MARKERS = ("bu sayfa", "bu ekran", "burada ne", "hangi ekran", "neredeyim", "ne işe yarıyor", "ne ise yariyor")


def _looks_like_page_help_question(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in _PAGE_HELP_MARKERS)


def _narrow_to_entity(data: Any, entity_id: Any) -> Any:
    if not isinstance(data, list):
        return data
    for row in data:
        if _extract_id(row) == entity_id:
            return [row]
    return []


class AssistantV2Service:
    def ask(
        self, user: Any, question: str, *, conversation_id: str | None = None, page_path: str | None = None
    ) -> AssistantAnswer:
        query = _clip_query(question)
        if not query:
            return self._ambiguous(user, None, reason="empty_question")

        state = get_conversation_state(user, conversation_id)
        # A supplied conversation_id that did NOT resolve to real, matching
        # session state (unknown id, foreign user, tampered/crafted id) is
        # discarded here, not just ignored for lookup purposes -- it must
        # never be echoed back downstream either (Phase M #12: a crafted
        # conversation_id belonging to another user must be treated as
        # fully foreign, not partially honored by reflecting it in the
        # response). Every branch below now starts a genuinely fresh
        # conversation in this case, never `conversation_id or start_new(...)`
        # against the untrusted original value.
        conversation_id = state.conversation_id if state else None

        # Safety classification runs FIRST, before follow-up resolution or
        # intent routing, and before any capability is even considered --
        # a SENSITIVE_REQUEST or OUT_OF_SCOPE question never reaches
        # capability_dispatcher at all (mandate Phase C).
        safety = classify_safety(query)
        if safety.category is SafetyCategory.SENSITIVE_REQUEST:
            return self._terminal(
                user, conversation_id, status=AssistantResultStatus.SENSITIVE_REQUEST,
                answer=(
                    "Bu istekte hassas kişisel veya idari bilgi görüntüleme talebi tespit ettim "
                    "(ör. performans puanı, amir görüşü, mesaj içeriği, kimlik/iletişim bilgisi). "
                    "Bu tür bilgileri asistan üzerinden göstermiyorum; ilgili yetkili ekrandan görüntüleyebilirsiniz."
                ),
            )
        if safety.category is SafetyCategory.OUT_OF_SCOPE:
            return self._terminal(
                user, conversation_id, status=AssistantResultStatus.OUT_OF_SCOPE,
                answer="Bu konu BYS360 kapsamı dışında; yalnızca BYS360 modülleri hakkında yardımcı olabilirim.",
            )

        # Procedural ("nasıl X yapılır" / "how do I...") guide routing is
        # tried BEFORE the generic conversational-intent check (mandate
        # Phase B/C): a specific, topic-scoped guide match (e.g. "kpi hedef
        # nasıl kullanılır") is more informative than the generic HELP
        # intent's canned answer, and guide_intent_router's absolute-score
        # floor (see its own module docstring) already filters out bare,
        # topic-less procedural phrasing that would otherwise collide with
        # a genuine "yardım et" / "nasıl kullanılır" HELP question -- a
        # guide only wins here at HIGH confidence with a real topic match.
        guide_resolution = resolve_guide_intent(query)
        if guide_resolution.tier is ConfidenceTier.HIGH and guide_resolution.best_guide_key:
            return self._answer_guide(user, query, conversation_id or start_new_conversation(user), guide_key=guide_resolution.best_guide_key)

        # Conversational intents (greeting/help/thanks/identity/capability
        # explanation) never touch capability_dispatcher -- there is no
        # authorization concept for "hello".
        conversational = detect_conversational(query)
        if conversational.intent is not ConversationalIntent.NONE:
            return self._terminal(
                user, conversation_id, status=AssistantResultStatus.CONVERSATIONAL_RESPONSE,
                answer=conversational.answer or "",
            )

        # Page-context "what is this screen for" questions (Phase D):
        # resolved server-side from a known path table, never from a
        # client-supplied module name, and never used for authorization.
        if page_path and _looks_like_page_help_question(query):
            page = resolve_page_context(page_path)
            explanation = explain_page(page)
            if explanation:
                return self._terminal(
                    user, conversation_id, status=AssistantResultStatus.CONVERSATIONAL_RESPONSE, answer=explanation,
                )

        follow_up = resolve_follow_up(query, state)

        if follow_up.is_follow_up and follow_up.ambiguous:
            return self._ambiguous(user, conversation_id or start_new_conversation(user), reason=follow_up.ambiguous_reason)

        if follow_up.is_follow_up and follow_up.capability_key:
            return self._answer_capability(
                user, query, conversation_id or start_new_conversation(user),
                capability_key=follow_up.capability_key,
                narrow_to_entity_id=follow_up.resolved_entity_id,
            )

        resolution = resolve_intent(query)
        if resolution.tier is ConfidenceTier.LOW:
            return self._ambiguous(user, conversation_id or start_new_conversation(user), reason="no_matching_capability")
        if resolution.tier is ConfidenceTier.MEDIUM:
            return self._ambiguous(
                user, conversation_id or start_new_conversation(user), reason="multiple_candidates",
                candidates=[c.capability_key for c in resolution.candidates],
            )

        cid = conversation_id or start_new_conversation(user)

        best_key = resolution.best_capability_key
        if best_key:
            extra_kwargs = _extra_kwargs_for(best_key, query)
            if _capability_needs_unavailable_parameters(best_key, available_kwargs=set(extra_kwargs)):
                # A HIGH-confidence single-capability match whose handler
                # still needs a specific record identifier (e.g. sicil_no)
                # this service has no value for from free text alone --
                # admitting that up front, never guessing a record
                # identifier and never attempting a call that would only
                # fail inside the handler.
                return self._ambiguous(user, cid, reason="missing_required_parameter", candidates=[best_key])

        # Free-text auto-routing to the one built cross-module combination
        # (personnel + incomplete-evaluation) is intentionally NOT done this
        # wave -- it needs a resolved unit/period entity pair from
        # entity_extraction plus a real decision about default period
        # selection that hasn't been reviewed yet. See
        # ask_cross_module_personnel_pending_evaluation() for the explicit,
        # already-authorized entry point a caller can use directly, and the
        # checkpoint report's "remaining gaps" for this specific omission.
        return self._answer_capability(user, query, cid, capability_key=resolution.best_capability_key, narrow_to_entity_id=None)

    def ask_cross_module_personnel_pending_evaluation(
        self, user: Any, question: str, *, conversation_id: str | None, birim: str, period_id: int
    ) -> AssistantAnswer:
        """Explicit entry point for the one built cross-module capability
        (Phase G worked example) -- not auto-routed from free text this
        wave (see ask()'s note), called directly when a caller already
        knows it wants this combination (e.g. a dedicated UI action)."""
        cid = conversation_id or start_new_conversation(user)
        cross_result = personnel_pending_evaluation_in_unit(user, birim=birim, period_id=period_id)
        composed = compose_cross_module_response(cross_result, question=question)
        entity_refs = _entity_refs_from_data(cross_result.data)
        record_turn(
            user, cid,
            capability_key=None,
            module_key=", ".join(cross_result.contributing_module_keys) or None,
            entity_refs=entity_refs,
            safe_summary=composed.answer_text,
            source_labels=list(cross_result.source_labels),
        )
        return AssistantAnswer(
            status=cross_result.status.value,
            answer=composed.answer_text,
            capability_key=None,
            module_keys=cross_result.contributing_module_keys,
            sources=tuple(SourceCard(label=label, url=None) for label in cross_result.source_labels[:MAX_SOURCE_COUNT]),
            conversation_id=cid,
            clarification=None,
            related_links=(),
        )

    def _answer_capability(
        self, user: Any, question: str, conversation_id: str, *, capability_key: str | None, narrow_to_entity_id: Any
    ) -> AssistantAnswer:
        if not capability_key:
            return self._ambiguous(user, conversation_id, reason="no_matching_capability")
        extra_kwargs = _extra_kwargs_for(capability_key, question)
        if _capability_needs_unavailable_parameters(capability_key, available_kwargs=set(extra_kwargs)):
            return self._ambiguous(user, conversation_id, reason="missing_required_parameter", candidates=[capability_key])

        result = invoke_capability(user, capability_key, **extra_kwargs)
        if narrow_to_entity_id is not None and result.status is AssistantResultStatus.DATA_FOUND:
            narrowed_data = _narrow_to_entity(result.data, narrow_to_entity_id)
            result = AssistantCapabilityResult(
                status=AssistantResultStatus.DATA_FOUND if narrowed_data else AssistantResultStatus.NO_DATA,
                message=result.message,
                capability_key=result.capability_key,
                module_key=result.module_key,
                data=narrowed_data or None,
                source_label=result.source_label,
            )

        composed = compose_response(result, question=question)
        entity_refs = _entity_refs_from_data(result.data)
        sources = _build_sources(user, result)
        related_links = _build_related_links_for_capability(user, result)

        record_turn(
            user, conversation_id,
            capability_key=result.capability_key,
            module_key=result.module_key,
            entity_refs=entity_refs,
            safe_summary=composed.answer_text,
            source_labels=[s.label for s in sources],
        )

        return AssistantAnswer(
            status=result.status.value,
            answer=composed.answer_text,
            capability_key=result.capability_key,
            module_keys=(result.module_key,) if result.module_key else (),
            sources=sources,
            conversation_id=conversation_id,
            clarification=None,
            related_links=related_links,
        )

    def _answer_guide(self, user: Any, question: str, conversation_id: str, *, guide_key: str) -> AssistantAnswer:
        result = invoke_guide(user, guide_key)
        composed = compose_guide_response(result, question=question)
        sources = _build_sources(user, result)
        related_links = _build_related_links_for_guide(user, result)

        record_turn(
            user, conversation_id,
            capability_key=result.capability_key,
            module_key=result.module_key,
            entity_refs=[],
            safe_summary=composed.answer_text,
            source_labels=[s.label for s in sources],
        )

        return AssistantAnswer(
            status=result.status.value,
            answer=composed.answer_text,
            capability_key=result.capability_key,
            module_keys=(result.module_key,) if result.module_key else (),
            sources=sources,
            conversation_id=conversation_id,
            clarification=None,
            related_links=related_links,
        )

    def _terminal(
        self, user: Any, conversation_id: str | None, *, status: AssistantResultStatus, answer: str
    ) -> AssistantAnswer:
        """A response produced entirely before any capability dispatch --
        SENSITIVE_REQUEST, OUT_OF_SCOPE, or CONVERSATIONAL_RESPONSE. Still
        recorded as a conversation turn (with capability_key=None, no
        entity_refs) so a subsequent genuine follow-up question correctly
        sees "no previous bounded list" rather than silently reusing an
        even-earlier turn's stale entity references."""
        cid = conversation_id or start_new_conversation(user)
        record_turn(
            user, cid, capability_key=None, module_key=None, entity_refs=[],
            safe_summary=answer, source_labels=[],
        )
        return AssistantAnswer(
            status=status.value, answer=answer, capability_key=None, module_keys=(),
            sources=(), conversation_id=cid, clarification=None, related_links=(),
        )

    def _ambiguous(
        self, user: Any, conversation_id: str | None, *, reason: str | None, candidates: list[str] | None = None
    ) -> AssistantAnswer:
        cid = conversation_id or start_new_conversation(user)
        return AssistantAnswer(
            status=AssistantResultStatus.AMBIGUOUS_REQUEST.value,
            answer="Bu isteği tam olarak anlayamadım. Lütfen daha spesifik bir şekilde belirtir misiniz?",
            capability_key=None,
            module_keys=(),
            sources=(),
            conversation_id=cid,
            clarification={"reason": reason, "candidates": candidates or []},
            related_links=(),
        )


__all__ = ["AssistantV2Service", "AssistantAnswer", "SourceCard"]
