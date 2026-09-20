# BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7
"""Assistant service extraction target for mobile routes."""
from __future__ import annotations

from typing import Any


# BYS360 Assistant V2 MOBILE BACKEND CUTOVER (mandate Phase I): the live
# mobile endpoint now answers via AssistantV2Service + MobilePresentationAdapter,
# not the independent rule-based `_bys360_legacy_mobile_b49_assistant_v2_ask`
# engine. Bearer auth, HTTP status behavior, and the exact JSON field names
# the live Flutter AssistantScreen reads are preserved -- only the answering
# engine changed. `metrics`/`user_label` are kept via the same, unchanged,
# already-shipped helper functions the legacy engine used (they are not
# part of AssistantV2Service's own contract, so they are computed here and
# merged in, exactly matching prior behavior for those two fields).
def delegate_mobile_b49_assistant_v2_ask(user: Any):
    import logging

    from flask import jsonify, request

    from app.api.mobile.domains.assistant_chat import _b49_safe_summary
    from app.api.mobile.shared import _full_name
    from app.services.assistant_v2.mobile_presentation_adapter import adapt_for_mobile
    from app.services.assistant_v2.service import AssistantV2Service

    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question") or payload.get("q") or payload.get("message") or "")

    try:
        answer = AssistantV2Service().ask(user, question)
        data = adapt_for_mobile(answer)
    except Exception:
        # AssistantV2Service.ask() already catches every capability/guide-
        # level failure internally (never raises from that layer) -- this
        # is a last-resort net for anything upstream (session/adapter code)
        # so the mobile client always gets the same safe JSON shape it
        # already knows how to render, never a raw 500/stack trace.
        logging.getLogger(__name__).exception("assistant_v2 mobile cutover: unexpected failure answering question")
        data = {
            "answer": "BYS360 Asistanı bu isteği işlerken bir sorunla karşılaştı; lütfen daha sonra tekrar deneyin.",
            "module": "BYS360 Asistanı", "route_hint": "", "required_roles": [],
            "steps": [], "warnings": [], "control_items": [], "suggested_questions": [],
            "intent": "SYSTEM_ERROR",
        }
    data["source"] = "bys360_mobile_assistant_v2_8_49"
    try:
        data["metrics"] = _b49_safe_summary(user)
        data["user_label"] = _full_name(user)
    except Exception:
        logging.getLogger(__name__).exception("assistant_v2 mobile cutover: metrics/user_label enrichment failed")
    return jsonify(data)
