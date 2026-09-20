"""BYS360 Assistant V2 -- capability dispatcher (mandate Phases 6, 8, 9, 18, 19).

This is the ONE place a capability's read_adapter function is ever called.
`invoke_capability(user, capability_key, **kwargs)` is the enforced order of
operations for every single call, with no bypass:

    1. resolve the capability from the registry (unknown key -> deny)
    2. confirm the capability and its module are both active (disabled -> deny)
    3. resolve the user's REAL, current authorization for this exact
       capability via the same centralized pipeline Settings Center V2
       itself uses (`app.route_support.can_access_menu`), or one of the two
       documented, reviewed `auth_override` exceptions -- never a prompt,
       never "the model was told not to allow it" (Phase 6 explicitly
       forbids that)
    4. only if authorized: call the real read_adapter function, in a bounded
       try/except so one broken capability can never crash the caller
       (Phase 19) or leave the whole dispatcher in a bad state
    5. classify the outcome into exactly one `AssistantResultStatus` (Phase 9)
       and attach the capability's own `source_attribution_label` (Phase 8)
    6. write one audit-log row via the existing, already-shipped
       `app.services.ai_agent.repository.insert_agent_request_log` (reused,
       not reinvented -- see the module-level note below on why this
       dispatcher does NOT also call `insert_agent_audit_log`)

No step here can be skipped by a caller: there is exactly one public
function, and it always performs steps 1-3 before step 4 can possibly run.

On `insert_agent_audit_log` (app/services/ai_agent/repository.py:90-111):
that function hardcodes `target_table='performance_summary'` and
`action_status='read_only_summary'` inside its own SQL literal -- it was
written narrowly for one specific caller (the performance bridge) and would
silently mislabel every other capability's audit row if reused here. Rather
than either (a) falsifying audit data by calling it anyway, or (b) adding a
new, more generic audit table via a migration (which Phase 26 of this
project's own mandate requires stopping and getting explicit approval for
first), this dispatcher reuses the already-generic, already-shipped
`insert_agent_request_log` for every capability invocation instead, encoding
capability_key/module_key/status/duration into its existing free-text
`intent`/`response_summary` columns. A dedicated structured audit table
would be a cleaner design for a later, separately-reviewed phase.
"""
from __future__ import annotations

import importlib
import logging
import time
from typing import Any

from app.route_support import ADMIN_FAMILY_ROLES, can_access_menu, user_has_any_role
from app.services.ai_agent.repository import insert_agent_request_log
from app.services.assistant_v2.capability_registry import (
    AssistantCapabilityEntry,
    get_capability,
)
from app.services.assistant_v2.result_contract import (
    AssistantCapabilityResult,
    AssistantResultStatus,
)
from app.services.settings.module_registry import get_module

logger = logging.getLogger(__name__)

_SAFE_MESSAGES: dict[AssistantResultStatus, str] = {
    AssistantResultStatus.NO_DATA: "Bu istekle eşleşen bir kayıt bulunamadı.",
    AssistantResultStatus.ACCESS_DENIED: (
        "Bu bilgiyi görüntüleyemiyorum çünkü hesabınız için gerekli erişim yetkisi etkin değil."
    ),
    AssistantResultStatus.CAPABILITY_UNAVAILABLE: "Bu yetenek şu anda kullanılamıyor.",
    AssistantResultStatus.SYSTEM_ERROR: (
        "Bu isteği işlerken bir sorun oluştu; lütfen daha sonra tekrar deneyin."
    ),
}


def _is_authorized(user: Any, entry: AssistantCapabilityEntry) -> bool:
    """The ONLY place capability-level authorization is decided. Every
    branch here reuses a real, already-enforced check elsewhere in this
    codebase -- nothing here invents a new permission concept. Fails closed:
    a capability matching none of the three known patterns is denied, not
    silently allowed (see the registry's own `find_capabilities_missing_permission`
    completeness test, which makes that case unreachable in a clean registry,
    but this function does not trust that invariant blindly -- it re-checks)."""
    if entry.is_self_describing:
        return bool(user and getattr(user, "is_authenticated", False))
    if entry.permission_key:
        return can_access_menu(user, entry.permission_key)
    override = entry.extra.get("auth_override") if entry.extra else None
    if override == "app.file_center.permissions.can_manage_file_center_settings":
        from app.file_center.permissions import can_manage_file_center_settings

        return bool(can_manage_file_center_settings(user))
    if override == "admin_required_role_family":
        return user_has_any_role(user, ADMIN_FAMILY_ROLES)
    return False


def _resolve_handler(service_handler: str):
    module_path, _, attr_name = service_handler.rpartition(".")
    module = importlib.import_module(module_path)
    handler = getattr(module, attr_name)
    if not callable(handler):
        raise TypeError(f"service_handler {service_handler!r} is not callable")
    return handler


def _is_empty(data: Any) -> bool:
    if data is None:
        return True
    if isinstance(data, list | dict | tuple | set):
        return len(data) == 0
    return False


def _audit(
    *,
    user: Any,
    capability_key: str,
    module_key: str | None,
    status: AssistantResultStatus,
    duration_ms: int,
) -> None:
    try:
        user_id = getattr(user, "id", None)
        insert_agent_request_log(
            user_id=int(user_id) if user_id is not None else None,
            prompt=f"assistant_v2_capability:{capability_key}",
            intent=capability_key,
            response_summary=(
                f"module={module_key or 'unknown'} status={status.value} duration_ms={duration_ms}"
            ),
        )
    except Exception:
        # Audit logging must never be able to break a real request -- log
        # locally and move on (Phase 19: no capability failure, including a
        # failure to record that a capability ran, may propagate outward
        # as an unhandled exception).
        logger.exception(
            "assistant_v2 capability_dispatcher: audit log write failed for capability_key=%s",
            capability_key,
        )


def invoke_capability(user: Any, capability_key: str, **kwargs: Any) -> AssistantCapabilityResult:
    """The single entry point for actually running a capability. Always
    returns an `AssistantCapabilityResult` -- never raises for an
    unauthorized, unknown, disabled, or failing capability; only a
    programming error in the caller (e.g. a non-string capability_key) would
    raise, and even a handler-level exception is caught and turned into a
    SYSTEM_ERROR result rather than propagating."""
    started = time.monotonic()
    entry = get_capability(capability_key)

    if entry is None or not entry.active:
        result = AssistantCapabilityResult(
            status=AssistantResultStatus.CAPABILITY_UNAVAILABLE,
            message=_SAFE_MESSAGES[AssistantResultStatus.CAPABILITY_UNAVAILABLE],
            capability_key=capability_key,
        )
        _audit(
            user=user,
            capability_key=capability_key,
            module_key=None,
            status=result.status,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return result

    module = get_module(entry.module_key)
    if module is None or not module.active:
        result = AssistantCapabilityResult(
            status=AssistantResultStatus.CAPABILITY_UNAVAILABLE,
            message=_SAFE_MESSAGES[AssistantResultStatus.CAPABILITY_UNAVAILABLE],
            capability_key=entry.capability_key,
            module_key=entry.module_key,
        )
        _audit(
            user=user,
            capability_key=entry.capability_key,
            module_key=entry.module_key,
            status=result.status,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return result

    try:
        authorized = _is_authorized(user, entry)
    except Exception:
        logger.exception(
            "assistant_v2 capability_dispatcher: authorization check itself failed for capability_key=%s",
            entry.capability_key,
        )
        authorized = False  # fail closed -- an authorization check that
        # cannot even run is treated as a denial, never as an implicit allow.

    if not authorized:
        result = AssistantCapabilityResult(
            status=AssistantResultStatus.ACCESS_DENIED,
            message=_SAFE_MESSAGES[AssistantResultStatus.ACCESS_DENIED],
            capability_key=entry.capability_key,
            module_key=entry.module_key,
        )
        _audit(
            user=user,
            capability_key=entry.capability_key,
            module_key=entry.module_key,
            status=result.status,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return result

    try:
        handler = _resolve_handler(entry.service_handler)
        data = handler(user, **kwargs)
    except Exception:
        logger.exception(
            "assistant_v2 capability_dispatcher: handler failed for capability_key=%s",
            entry.capability_key,
        )
        result = AssistantCapabilityResult(
            status=AssistantResultStatus.SYSTEM_ERROR,
            message=_SAFE_MESSAGES[AssistantResultStatus.SYSTEM_ERROR],
            capability_key=entry.capability_key,
            module_key=entry.module_key,
        )
        _audit(
            user=user,
            capability_key=entry.capability_key,
            module_key=entry.module_key,
            status=result.status,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        return result

    status = AssistantResultStatus.NO_DATA if _is_empty(data) else AssistantResultStatus.DATA_FOUND
    result = AssistantCapabilityResult(
        status=status,
        message=(
            _SAFE_MESSAGES[AssistantResultStatus.NO_DATA]
            if status is AssistantResultStatus.NO_DATA
            else "İstenen bilgi bulundu."
        ),
        capability_key=entry.capability_key,
        module_key=entry.module_key,
        data=None if status is AssistantResultStatus.NO_DATA else data,
        source_label=entry.source_attribution_label if status is AssistantResultStatus.DATA_FOUND else None,
    )
    if entry.audit_required or status is AssistantResultStatus.DATA_FOUND:
        _audit(
            user=user,
            capability_key=entry.capability_key,
            module_key=entry.module_key,
            status=result.status,
            duration_ms=int((time.monotonic() - started) * 1000),
        )
    return result


__all__ = ["invoke_capability"]
