"""BYS360 Assistant V2 -- server-side page context resolution (mandate
Phase D).

The client may tell the assistant "the user is currently looking at this
URL path" (completely normal -- the browser genuinely knows its own current
page). What this module does NOT do is trust that as authorization or as a
module NAME: it looks the path up against `_PATH_PREFIXES`, a small,
server-owned, hardcoded table mapping real BYS360 URL prefixes to real
`module_key` values from `app.services.settings.module_registry`, and
returns only a `PageContext` built from that table -- never anything the
client supplied verbatim. An unrecognized path resolves to `module_key=None`
(no page-specific context), never a guess.

Page context only ever influences WHICH conversational/explanatory text is
shown; it is never passed to `capability_dispatcher` and never used to
decide whether a capability is authorized -- that decision continues to
come exclusively from the real, live authenticated user's role, exactly as
in every other part of this project.

The path->module_key table below covers the same real BYS360 screens the
legacy chain's own `PAGE_TOPIC_PREFIXES_V32` table already covers
(`app/services/ai_agent/assistant_chatgpt_like_v31.py`), re-derived against
this project's real module_key vocabulary (16 modules) rather than the
legacy chain's own topic-key vocabulary.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.settings.module_registry import get_module

_PATH_PREFIXES: tuple[tuple[str, str], ...] = (
    ("/performance", "performance_mgmt"),
    ("/performans", "performance_mgmt"),
    ("/personnel", "personnel_hr"),
    ("/admin/users", "personnel_hr"),
    ("/hr-management", "personnel_hr"),
    ("/leave", "personnel_hr"),
    ("/delegation", "personnel_hr"),
    ("/settings/role-matrix", "settings_auth"),
    ("/admin/role-matrix", "settings_auth"),
    ("/settings-center", "settings_auth"),
    ("/settings", "settings_auth"),
    ("/support", "support_help"),
    ("/surveys", "surveys"),
    ("/messages", "communication"),
    ("/communication", "communication"),
    ("/portal", "portal"),
    ("/file-center", "file_center"),
    ("/dosya-merkezi", "file_center"),
    ("/ai/decision-support", "ai_decision_support"),
    ("/ai-agent", "virtual_assistant"),
    ("/dashboard", "dashboard"),
    ("/notifications", "notifications"),
)


@dataclass(frozen=True)
class PageContext:
    path: str | None
    module_key: str | None
    module_display_name: str | None


def resolve_page_context(path: str | None) -> PageContext:
    """Never raises. An unrecognized/absent path yields an all-None
    PageContext -- the caller must not fabricate a module for it."""
    normalized_path = str(path or "").strip()
    if not normalized_path:
        return PageContext(path=None, module_key=None, module_display_name=None)

    for prefix, module_key in _PATH_PREFIXES:
        if normalized_path == prefix or normalized_path.startswith(prefix + "/"):
            module = get_module(module_key)
            return PageContext(
                path=normalized_path,
                module_key=module_key,
                module_display_name=module.display_name if module else None,
            )
    return PageContext(path=normalized_path, module_key=None, module_display_name=None)


def explain_page(context: PageContext) -> str | None:
    """Returns a safe, generic explanation sentence for a resolved page
    context, or None if the page wasn't recognized (the caller should then
    fall back to a generic "I don't have specific information about this
    page" answer rather than inventing one)."""
    if not context.module_key or not context.module_display_name:
        return None
    return (
        f"Şu anda {context.module_display_name} modülü ekranındasınız. "
        f"Bu modülle ilgili erişim yetkiniz dahilinde soru sorabilirsiniz."
    )


__all__ = ["PageContext", "resolve_page_context", "explain_page"]
