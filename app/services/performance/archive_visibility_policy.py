from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

# BYS360_PERFORMANCE_COMPLETION_PHASE7_ARCHIVE_VISIBILITY_BRIDGE
try:
    from app.services.performance.phase7_scorecard_archive_center import (
        filter_phase7_archive_records,
        resolve_phase7_archive_visibility,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/archive_visibility_policy.py:11")
