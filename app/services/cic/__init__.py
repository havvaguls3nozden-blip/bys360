"""Canonical Corporate Information Center service package."""

from __future__ import annotations

from . import (
    access_policy as access_policy,
    celebration_service as celebration_service,
    mail_service as mail_service,
    query_service as query_service,
    scheduler_service as scheduler_service,
    service as service,
    template_service as template_service,
)

__all__ = [
    "access_policy",
    "query_service",
    "template_service",
    "mail_service",
    "scheduler_service",
    "celebration_service",
    "service",
]
