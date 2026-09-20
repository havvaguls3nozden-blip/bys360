"""BYS360 Assistant V2 -- procedural guide dispatcher (mandate Phase C).

Mirrors `capability_dispatcher.invoke_capability`'s enforced order of
operations exactly, scoped to `procedural_guides.PROCEDURAL_GUIDE_REGISTRY`
instead of the data-capability registry: resolve -> confirm active -> check
REAL live authorization (`app.route_support.can_access_menu`, re-run every
call, never cached) -> only then build the informational result -> audit.
A guide never calls a database read at all -- its "data" is the static
`steps`/`warnings` text authored in the registry -- so there is no handler
call and therefore no SYSTEM_ERROR path (unlike capabilities, a guide cannot
fail mid-read; it can only be unknown, disabled, or unauthorized).
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.route_support import can_access_menu
from app.services.ai_agent.repository import insert_agent_request_log
from app.services.assistant_v2.procedural_guides import ProceduralGuideEntry, get_guide
from app.services.assistant_v2.result_contract import (
    AssistantCapabilityResult,
    AssistantResultStatus,
)
from app.services.settings.module_registry import get_module

logger = logging.getLogger(__name__)

GUIDE_SOURCE_LABEL = "BYS360 Kullanım Rehberi"

_SAFE_MESSAGES: dict[AssistantResultStatus, str] = {
    AssistantResultStatus.ACCESS_DENIED: (
        "Bu rehberi görüntüleyemiyorum çünkü hesabınız için gerekli erişim yetkisi etkin değil."
    ),
    AssistantResultStatus.CAPABILITY_UNAVAILABLE: "Bu kullanım rehberi şu anda kullanılamıyor.",
}


def _is_authorized(user: Any, entry: ProceduralGuideEntry) -> bool:
    if entry.required_permission is None:
        # Same documented pattern as File Center's capabilities (module
        # predates the menu-key pipeline) -- login-gated only, never a new
        # authorization concept.
        return bool(user and getattr(user, "is_authenticated", False))
    return can_access_menu(user, entry.required_permission)


def _audit(*, user: Any, guide_key: str, module_key: str | None, status: AssistantResultStatus, duration_ms: int) -> None:
    try:
        user_id = getattr(user, "id", None)
        insert_agent_request_log(
            user_id=int(user_id) if user_id is not None else None,
            prompt=f"assistant_v2_guide:{guide_key}",
            intent=guide_key,
            response_summary=f"module={module_key or 'unknown'} status={status.value} duration_ms={duration_ms}",
        )
    except Exception:
        logger.exception("assistant_v2 guide_dispatcher: audit log write failed for guide_key=%s", guide_key)


def invoke_guide(user: Any, guide_key: str) -> AssistantCapabilityResult:
    """Always returns an `AssistantCapabilityResult` (same contract
    capabilities use, so response_composer/service.py can treat a guide
    answer uniformly) -- never raises."""
    started = time.monotonic()
    entry = get_guide(guide_key)

    if entry is None or not entry.active:
        result = AssistantCapabilityResult(
            status=AssistantResultStatus.CAPABILITY_UNAVAILABLE,
            message=_SAFE_MESSAGES[AssistantResultStatus.CAPABILITY_UNAVAILABLE],
            capability_key=guide_key,
        )
        _audit(user=user, guide_key=guide_key, module_key=None, status=result.status, duration_ms=int((time.monotonic() - started) * 1000))
        return result

    module = get_module(entry.module_key)
    if module is None or not module.active:
        result = AssistantCapabilityResult(
            status=AssistantResultStatus.CAPABILITY_UNAVAILABLE,
            message=_SAFE_MESSAGES[AssistantResultStatus.CAPABILITY_UNAVAILABLE],
            capability_key=entry.guide_key,
            module_key=entry.module_key,
        )
        _audit(user=user, guide_key=entry.guide_key, module_key=entry.module_key, status=result.status, duration_ms=int((time.monotonic() - started) * 1000))
        return result

    try:
        authorized = _is_authorized(user, entry)
    except Exception:
        logger.exception("assistant_v2 guide_dispatcher: authorization check itself failed for guide_key=%s", entry.guide_key)
        authorized = False

    if not authorized:
        result = AssistantCapabilityResult(
            status=AssistantResultStatus.ACCESS_DENIED,
            message=_SAFE_MESSAGES[AssistantResultStatus.ACCESS_DENIED],
            capability_key=entry.guide_key,
            module_key=entry.module_key,
        )
        _audit(user=user, guide_key=entry.guide_key, module_key=entry.module_key, status=result.status, duration_ms=int((time.monotonic() - started) * 1000))
        return result

    data = {
        "title": entry.title,
        "summary": entry.summary,
        "steps": list(entry.steps),
        "warnings": list(entry.warnings),
    }
    result = AssistantCapabilityResult(
        status=AssistantResultStatus.DATA_FOUND,
        message="İstenen kullanım rehberi bulundu.",
        capability_key=entry.guide_key,
        module_key=entry.module_key,
        data=data,
        source_label=GUIDE_SOURCE_LABEL,
    )
    _audit(user=user, guide_key=entry.guide_key, module_key=entry.module_key, status=result.status, duration_ms=int((time.monotonic() - started) * 1000))
    return result


__all__ = ["invoke_guide", "GUIDE_SOURCE_LABEL"]
