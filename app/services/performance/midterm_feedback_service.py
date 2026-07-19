from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

# BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_SERVICE_BRIDGE
try:
    from app.services.performance.phase8_midterm_feedback_center import (
        build_phase8_evaluator_reminders,
        build_phase8_scorecard_summary,
        filter_phase8_midterm_notes,
        normalize_phase8_midterm_note,
        phase8_midterm_contract,
        phase8_note_type_label,
        phase8_status_label,
        phase8_visibility_label,
        resolve_phase8_midterm_visibility,
        seed_phase8_midterm_feedback_settings,
        validate_phase8_midterm_note,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/midterm_feedback_service.py:20")
