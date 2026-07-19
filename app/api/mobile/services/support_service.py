# BYS360_MOBILE_SERVICE_SCAFFOLD_P1_2_V2_17_7
"""Support ticket service extraction target for mobile routes."""
from __future__ import annotations


def mobile_support_ticket_create(user, legacy_handler):
    """Delegated mobile support ticket creation handler."""
    return legacy_handler(user)

def mobile_support_ticket_reply(user, ticket_id, legacy_handler):
    """Delegated mobile support ticket reply handler."""
    return legacy_handler(user, ticket_id)
