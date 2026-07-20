"""Canonical Corporate Information Center service package."""

from __future__ import annotations

from . import access_policy as access_policy
from . import celebration_service as celebration_service
from . import mail_service as mail_service
from . import query_service as query_service
from . import scheduler_service as scheduler_service
from . import service as service
from . import template_service as template_service

__all__ = [
    "access_policy",
    "query_service",
    "template_service",
    "mail_service",
    "scheduler_service",
    "celebration_service",
    "service",
]
