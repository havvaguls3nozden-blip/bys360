from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

# BYS360_PERFORMANCE_COMPLETION_PHASE8_SCORECARD_NOTES_BRIDGE
try:
    from app.services.performance.phase8_midterm_feedback_center import (
        build_phase8_scorecard_summary,
        phase8_note_type_label,
        phase8_status_label,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/scorecard_midterm_notes.py:12")
