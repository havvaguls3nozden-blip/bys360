
"""Facade-protected package for Corporate Information Center service split.

P5 creates this package as a safe bridge. It does not replace the legacy module yet.
"""
from __future__ import annotations

from . import repository as repository  # noqa: F401
from . import query_service as query_service  # noqa: F401
from . import template_service as template_service  # noqa: F401
from . import mail_service as mail_service  # noqa: F401
from . import scheduler_service as scheduler_service  # noqa: F401
from . import celebration_service as celebration_service  # noqa: F401

__all__ = [
    "repository",
    "query_service",
    "template_service",
    "mail_service",
    "scheduler_service",
    "celebration_service",
]
