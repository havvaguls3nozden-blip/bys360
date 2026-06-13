# -*- coding: utf-8 -*-
from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

# BYS360_PERFORMANCE_COMPLETION_PHASE9_EVALUATOR_GUIDANCE_BRIDGE
try:
    from app.services.performance.phase9_development_guidance_center import (
        build_phase9_evaluator_guidance_context,
        resolve_phase9_guidance_visibility,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/evaluator_development_guidance.py:11")
