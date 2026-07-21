from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_SERVICE_BRIDGE
try:
    from app.services.performance.phase9_development_guidance_center import (
        build_phase9_evaluator_guidance_context,
        build_phase9_scorecard_guidance_summary,
        filter_phase9_guidance_items,
        normalize_phase9_guidance,
        phase9_guidance_contract,
        phase9_guidance_type_label,
        phase9_priority_label,
        phase9_source_label,
        phase9_status_label,
        resolve_phase9_guidance_visibility,
        seed_phase9_development_guidance_settings,
        validate_phase9_guidance,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/development_guidance_service.py:21")
