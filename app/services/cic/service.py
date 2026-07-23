"""Canonical public service entry point for Corporate Information Center."""

from __future__ import annotations

from .access_policy import can_manage as can_manage
from .celebration_service import (
    celebration_context as celebration_context,
    ensure_celebration_schema as ensure_celebration_schema,
    import_celebration_dates_from_excel as import_celebration_dates_from_excel,
    save_celebration_settings as save_celebration_settings,
)
from .config_context import ensure_defaults as ensure_defaults
from .mail_service import send_task as send_task
from .misc_context import context as context
from .save_context import (
    save_recipients as save_recipients,
    save_system as save_system,
    save_tasks as save_tasks,
)
from .scheduler_service import run_due_tasks as run_due_tasks
from .template_service import save_templates as save_templates

__all__ = [
    "can_manage",
    "celebration_context",
    "context",
    "ensure_celebration_schema",
    "ensure_defaults",
    "import_celebration_dates_from_excel",
    "run_due_tasks",
    "save_celebration_settings",
    "save_recipients",
    "save_system",
    "save_tasks",
    "save_templates",
    "send_task",
]
