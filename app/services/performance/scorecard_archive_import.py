# -*- coding: utf-8 -*-
from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

# BYS360_PERFORMANCE_COMPLETION_PHASE7_ARCHIVE_IMPORT_BRIDGE
try:
    from app.services.performance.phase7_scorecard_archive_center import (
        normalize_phase7_archive_record,
        phase7_required_import_columns,
        validate_phase7_archive_record,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/scorecard_archive_import.py:12")
