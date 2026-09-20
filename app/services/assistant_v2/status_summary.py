"""BYS360 Assistant V2 -- safe status summary for Settings Center V2.

BYS360 Native AI Only: this module has ZERO dependency on `app.services.ai`
(no provider mode, no model name, no API key state) -- there is no external
provider to report on, since BYS360 Assistant V2 answers questions using its
own capability registry, authorization engine, and native Turkish response
composer, never a third-party model. Every field returned here is safe to
show any admin who can reach the Assistant V2 Settings Center page.
"""
from __future__ import annotations

from typing import Any

from app.services.assistant_v2.capability_registry import ASSISTANT_CAPABILITY_REGISTRY
from app.services.assistant_v2.procedural_guides import list_active_guides
from app.services.settings.module_registry import get_module, list_active_modules


def get_assistant_v2_status_summary() -> dict[str, Any]:
    registry = ASSISTANT_CAPABILITY_REGISTRY
    module_keys_with_coverage = {entry.module_key for entry in registry}
    active_module_keys = {m.module_key for m in list_active_modules()}
    read_count = sum(1 for e in registry if e.read_or_write == "read")
    write_count = sum(1 for e in registry if e.read_or_write == "write")

    virtual_assistant_entry = get_module("virtual_assistant")

    return {
        "bys360_ai_core_active": bool(virtual_assistant_entry and virtual_assistant_entry.active),
        "native_intent_engine_status": "Etkin (BYS360 yerli kural/sözlük tabanlı motor)",
        "module_count_total": len(active_module_keys),
        "module_count_with_coverage": len(module_keys_with_coverage & active_module_keys),
        "module_count_without_coverage": len(active_module_keys - module_keys_with_coverage),
        "capability_count_total": len(registry),
        "capability_count_read": read_count,
        "capability_count_write": write_count,
        "cross_module_intelligence_count": 1,  # cross_module_orchestrator.py: personnel_hr + performance_mgmt
        "procedural_guide_count": len(list_active_guides()),
        "authorization_enforcement_status": "Etkin (menu_key_required / build_menu_visibility_map ile aynı yetki hattı)",
        "source_attribution_status": "Etkin",
        "audit_status": "Etkin",
        "conversation_context_status": "Etkin (oturum bazlı, sınırlı, kimliği doğrulanmış her istekte yeniden yetkilendirilir)",
        "network_independence_status": "Etkin (harici ağ bağlantısı gerektirmez)",
        "external_ai_dependency_count": 0,
        # Phase F/I cutover status: both the normal web chat route
        # (/ai-agent/api/ask) and the mobile backend route
        # (/api/mobile/assistant/v2/ask) now answer via AssistantV2Service --
        # this field only ever reflects a real, already-completed code
        # change (app/ai_agent/routes.py, app/api/mobile/services/assistant_service.py),
        # never a status claimed ahead of the actual cutover.
        "web_backend_status": "Assistant V2",
        "mobile_backend_status": "Assistant V2",
        # Phase B/G of the single-intelligence-engine wave: both the web
        # widget's local KNOWLEDGE-table fallback
        # (bys360_assistant_module_memory_v30.js / bys360_assistant_module.js)
        # and the Flutter AssistantScreen's local keyword fallback
        # (mobile_flutter/.../assistant_screen.dart) now answer a failed
        # server call with exactly one fixed, deterministic "unavailable"
        # message, never a locally-computed business answer -- mechanically
        # verified (grep: zero live call sites into the old answer
        # functions; `flutter analyze`: 0 issues) before this flag is set
        # True. This field must only ever reflect that already-completed,
        # already-verified state, never be set ahead of it.
        "single_intelligence_engine_active": True,
    }


__all__ = ["get_assistant_v2_status_summary"]
