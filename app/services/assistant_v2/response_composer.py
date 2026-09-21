"""BYS360 Assistant V2 -- BYS360-native response composer (mandate: BYS360
Native AI Only, zero third-party AI dependency).

CRITICAL ARCHITECTURE PROPERTY: this module has ZERO runtime dependency on
`app.services.ai` (or any other AI-provider abstraction). It imports nothing
from that package, calls no HTTP endpoint, and constructs no external model
prompt. Every answer is built by plain Python string formatting over
already-authorized, already-structured capability data, using the
Turkish-language helpers in `language_helpers.py`. This property is proven,
not just asserted, by
`tests/quality/test_assistant_v2_external_ai_absence_contract_v1.py` (an
architectural AST-import scan) and by
`tests/quality/test_assistant_v2_network_independence_contract_v1.py` (which
blocks all outbound sockets and re-runs the full answer pipeline).

Non-DATA_FOUND short-circuit (unchanged from the prior design, still
correct): for every status other than DATA_FOUND, the dispatcher's own
`result.message` is already the safe, final answer -- no further composition
happens for ACCESS_DENIED / NO_DATA / CAPABILITY_UNAVAILABLE /
AMBIGUOUS_REQUEST / SYSTEM_ERROR.

For DATA_FOUND, `compose_response()` renders natural Turkish using a small
set of operation_type-driven generic renderers (list/search/summarize/
read_record/explain), plus one flagship, hand-written renderer for the
Phase G cross-module worked example
("Biriminizde performans değerlendirmesi tamamlanmamış N personel
bulunuyor: ...") via `compose_cross_module_response()`. Nothing here is a
canned/demo string independent of the actual capability data -- every
sentence is built from the real `result.data` that was already authorized
and returned by a real capability handler.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.services.assistant_v2.capability_registry import get_capability
from app.services.assistant_v2.language_helpers import (
    count_phrase,
    format_bytes_tr,
    format_date_tr,
    format_list_tr,
    no_data_phrase,
    source_attribution_phrase,
)
from app.services.assistant_v2.result_contract import (
    AssistantCapabilityResult,
    AssistantResultStatus,
)

logger = logging.getLogger(__name__)

_LABEL_FIELD_PRIORITY = (
    "title", "full_name", "display_name", "label", "ad_soyad",
    "sicil_no", "name", "policy_label", "role_label", "id",
)


@dataclass(frozen=True)
class ComposedResponse:
    answer_text: str
    status: AssistantResultStatus
    capability_key: str | None = None
    module_key: str | None = None
    source_label: str | None = None
    used_llm: bool = False  # always False in the native architecture; kept
    # for shape-compatibility with any caller that still inspects this field.


def _extract_item_label(row: Any) -> str | None:
    if isinstance(row, dict):
        for field_name in _LABEL_FIELD_PRIORITY:
            value = row.get(field_name)
            if value not in (None, ""):
                return str(value)
        return None
    if row is None:
        return None
    return str(row)


def _extract_item_labels(data: list[Any], *, max_items: int = 8) -> list[str]:
    labels: list[str] = []
    for row in data[:max_items]:
        label = _extract_item_label(row)
        if label:
            labels.append(label)
    return labels


def _render_list_like(*, display_name: str, data: list[Any]) -> str:
    count = len(data)
    if count == 0:
        return no_data_phrase(display_name)
    labels = _extract_item_labels(data)
    phrase = count_phrase(count, display_name)
    if labels:
        return f"{phrase} bulundu: {format_list_tr(labels)}."
    return f"{phrase} bulundu."


# Central raw-field guard (mandate: user-facing structured result
# humanization, Goal B). These are pure internal identifiers with no
# narratable end-user meaning even if relabeled -- omitted entirely from
# the generic dict-shaped fallback below, regardless of which capability
# produced them. This is the "unknown structured fields" safety net the
# mandate asks for; a capability whose data genuinely needs richer,
# domain-aware phrasing gets its own entry in _CAPABILITY_FORMATTERS
# instead (see file_center_read_quota_status below).
_OMITTED_TECHNICAL_FIELDS = frozenset({
    "user_id", "unit_id", "menu_key", "capability_key", "source_type",
})

# Field names with real end-user meaning but an internal snake_case name
# -- relabeled to a Turkish phrase instead of hidden, since dropping a
# genuine creation/update date would lose real information (e.g. for an
# audit-log-detail capability, "when" is the whole point).
_RELABELED_DATE_FIELDS: dict[str, str] = {
    "created_at": "Oluşturulma",
    "updated_at": "Güncellenme",
}


def _render_dict_summary(*, display_name: str, data: dict[str, Any]) -> str:
    if not data:
        return no_data_phrase(display_name)
    parts: list[str] = []
    for key, value in data.items():
        if value in (None, "") or key in _OMITTED_TECHNICAL_FIELDS:
            continue
        if key in _RELABELED_DATE_FIELDS:
            parts.append(f"{_RELABELED_DATE_FIELDS[key]}: {format_date_tr(value) or value}")
            continue
        parts.append(f"{key}: {value}")
    if not parts:
        return no_data_phrase(display_name)
    return f"{display_name}: " + ", ".join(parts) + "."


def _render_scalar(*, display_name: str, data: Any) -> str:
    if data in (None, "", [], {}):
        return no_data_phrase(display_name)
    return f"{display_name}: {data}."


def _render_generic(*, display_name: str, operation_type: str, data: Any) -> str:
    """Operation-type-driven generic renderer: every one of the 47
    capabilities falls back to one of these three shapes based on what
    Python type its adapter actually returned -- list -> list-like phrasing,
    dict -> key:value phrasing, anything else -> scalar phrasing. This is
    deliberately shape-based rather than a 47-way if/elif on capability_key,
    so a new capability gets a sensible native answer automatically without
    needing its own bespoke renderer."""
    if isinstance(data, list):
        return _render_list_like(display_name=display_name, data=data)
    if isinstance(data, dict):
        return _render_dict_summary(display_name=display_name, data=data)
    return _render_scalar(display_name=display_name, data=data)


def _format_file_center_quota_status(data: dict[str, Any]) -> str:
    """Domain-aware formatter for `file_center_read_quota_status` (mandate:
    user-facing structured result humanization, Goal A). Renders only the
    facts genuinely present in `data` -- never a quota limit, remaining
    quota, or percentage, since the reported production result carried
    none of those (an inactive/absent FileQuotaPolicy row)."""
    used_bytes_raw = data.get("total_used_bytes")
    used_bytes = int(used_bytes_raw) if isinstance(used_bytes_raw, (int, float)) else 0
    file_count_raw = data.get("total_file_count")
    file_count = int(file_count_raw) if isinstance(file_count_raw, (int, float)) else 0
    return (
        f"Dosya Merkezi'nde toplam {format_bytes_tr(used_bytes)} alan kullanılıyor.\n"
        f"Toplam {count_phrase(file_count, 'dosya')} bulunuyor."
    )


# Capability-specific formatters, checked before the generic shape-based
# renderer (mandate Goal B: "capability-specific formatter where domain
# meaning matters"). A small dict dispatch, not a growing if/elif chain --
# adding a new one is a one-line registration, never a change to
# compose_response()'s own control flow.
_CAPABILITY_FORMATTERS: dict[str, Any] = {
    "file_center_read_quota_status": _format_file_center_quota_status,
}


def compose_response(result: AssistantCapabilityResult, *, question: str = "") -> ComposedResponse:
    """The single public entry point for a single-capability result. Always
    returns a `ComposedResponse` -- never raises."""
    if result.status is not AssistantResultStatus.DATA_FOUND:
        return ComposedResponse(
            answer_text=result.message,
            status=result.status,
            capability_key=result.capability_key,
            module_key=result.module_key,
        )

    entry = get_capability(result.capability_key) if result.capability_key else None
    display_name = entry.display_name if entry else (result.capability_key or "Sonuç")
    operation_type = entry.operation_type if entry else "LIST"

    formatter = _CAPABILITY_FORMATTERS.get(result.capability_key) if result.capability_key else None

    try:
        if formatter is not None and isinstance(result.data, dict):
            answer = formatter(result.data)
        else:
            answer = _render_generic(display_name=display_name, operation_type=operation_type, data=result.data)
    except Exception:
        logger.exception(
            "assistant_v2 response_composer: native rendering failed for capability_key=%s",
            result.capability_key,
        )
        answer = f"{display_name} için sonuç bulundu, ancak biçimlendirilirken bir sorun oluştu."

    source_phrase = source_attribution_phrase([result.source_label] if result.source_label else [])
    if source_phrase:
        answer = f"{answer}\n\n{source_phrase}"

    return ComposedResponse(
        answer_text=answer,
        status=result.status,
        capability_key=result.capability_key,
        module_key=result.module_key,
        source_label=result.source_label,
    )


def compose_guide_response(result: AssistantCapabilityResult, *, question: str = "") -> ComposedResponse:
    """Composer for a procedural-guide result (mandate Phase B/C).
    `result.data` is always the fixed shape
    `{"title", "summary", "steps": [...], "warnings": [...]}` built by
    `guide_dispatcher.invoke_guide` -- rendered as a numbered step list
    rather than the generic dict-summary renderer (which would read as an
    ugly key:value dump for this shape)."""
    if result.status is not AssistantResultStatus.DATA_FOUND:
        return ComposedResponse(
            answer_text=result.message,
            status=result.status,
            capability_key=result.capability_key,
            module_key=result.module_key,
        )

    data = result.data if isinstance(result.data, dict) else {}
    title = str(data.get("title") or "Kullanım Rehberi")
    summary = str(data.get("summary") or "")
    steps = [str(s) for s in (data.get("steps") or [])]
    warnings = [str(w) for w in (data.get("warnings") or [])]

    lines = [title]
    if summary:
        lines.append(summary)
    if steps:
        lines.append("")
        lines.extend(f"{index}. {step}" for index, step in enumerate(steps, start=1))
    if warnings:
        lines.append("")
        lines.extend(f"Not: {warning}" for warning in warnings)
    answer = "\n".join(lines)

    source_phrase = source_attribution_phrase([result.source_label] if result.source_label else [])
    if source_phrase:
        answer = f"{answer}\n\n{source_phrase}"

    return ComposedResponse(
        answer_text=answer,
        status=result.status,
        capability_key=result.capability_key,
        module_key=result.module_key,
        source_label=result.source_label,
    )


def compose_cross_module_response(result: Any, *, question: str = "") -> ComposedResponse:
    """Composer for `cross_module_orchestrator.CrossModuleResult` objects.
    Kept as a separate function (rather than overloading compose_response)
    because the cross-module result shape genuinely differs -- plural
    `contributing_capability_keys`/`source_labels`, no single capability_key."""
    if result.status is not AssistantResultStatus.DATA_FOUND:
        return ComposedResponse(
            answer_text=result.message,
            status=result.status,
            module_key=", ".join(result.contributing_module_keys) or None,
        )

    data = result.data or []
    if result.contributing_capability_keys == (
        "personnel_hr_list_personnel",
        "performance_mgmt_list_incomplete_evaluations",
    ):
        # Flagship, hand-written phrasing for the mandate's own worked
        # example -- still built entirely from result.data, not a canned
        # string.
        names = _extract_item_labels(data)
        answer = (
            f"Biriminizde performans değerlendirmesi tamamlanmamış "
            f"{count_phrase(len(data), 'personel')} bulunuyor"
            + (f": {format_list_tr(names)}." if names else ".")
        )
    else:
        labels = _extract_item_labels(data)
        answer = (
            f"{count_phrase(len(data), 'kayıt')} bulundu"
            + (f": {format_list_tr(labels)}." if labels else ".")
        )

    source_phrase = source_attribution_phrase(list(result.source_labels))
    if source_phrase:
        answer = f"{answer}\n\n{source_phrase}"

    return ComposedResponse(
        answer_text=answer,
        status=result.status,
        module_key=", ".join(result.contributing_module_keys) or None,
        source_label=source_phrase or None,
    )


__all__ = ["ComposedResponse", "compose_response", "compose_guide_response", "compose_cross_module_response"]
