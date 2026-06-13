from __future__ import annotations



from flask_login import current_user

from .audit import log_ai_request, upsert_ai_summary_cache
from .client import get_ai_client
from .guardrails import ensure_ai_access, sanitize_output_text
from .prompts import get_prompt_definition
from .query_adapters import get_support_ticket_payload


def build_support_ticket_triage_response(ticket_id: int) -> dict:
    policy = ensure_ai_access("support", "triage")
    ticket, payload = get_support_ticket_payload(ticket_id)

    prompt = get_prompt_definition("support", "triage")
    user_prompt = (
        "Aşağıdaki destek talebi için kurumsal triage özeti üret. "
        "Talep özeti, öncelik yorumu, yönlendirme önerisi ve ilk işlem adımını kısa yaz:\n"
        f"{payload}"
    )
    result = get_ai_client().generate(
        system_prompt=prompt["system"],
        user_prompt=user_prompt,
        prompt_version=prompt["version"],
    )
    summary_text = sanitize_output_text(result.text)
    log_row = log_ai_request(
        module_type="support",
        feature_type="triage",
        target_table="support_tickets",
        target_id=ticket.id,
        user_id=getattr(current_user, "id", None),
        request_text=user_prompt,
        response_text=summary_text,
        provider_name=result.provider_name,
        model_name=result.model_name,
        prompt_version=result.prompt_version,
        latency_ms=result.latency_ms,
        token_in=result.token_in,
        token_out=result.token_out,
        was_masked=True,
        was_user_visible=policy.user_visible,
    )
    upsert_ai_summary_cache(
        module_type="support",
        target_table="support_tickets",
        target_id=ticket.id,
        summary_kind="triage",
        summary_text=summary_text,
    )
    return {
        "ok": True,
        "data": {
            "ticket_id": ticket.id,
            "summary": summary_text,
            "current_priority": ticket.priority,
            "current_status": ticket.status,
            "ai_request_log_id": log_row.id if log_row else None,
        },
    }