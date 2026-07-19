from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

# BYS360_PERFORMANCE_COMPLETION_PHASE9_SCORECARD_GUIDANCE_BRIDGE
try:
    from app.services.performance.phase9_development_guidance_center import (
        build_phase9_scorecard_guidance_summary,
        phase9_guidance_type_label,
        phase9_priority_label,
        phase9_status_label,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/scorecard_development_guidance.py:13")
