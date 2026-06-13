# -*- coding: utf-8 -*-
from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

# BYS360_PERFORMANCE_COMPLETION_PHASE7_ARCHIVE_SERVICE_BRIDGE
try:
    from app.services.performance.phase7_scorecard_archive_center import (
        calculate_phase7_archive_summary,
        filter_phase7_archive_records,
        normalize_phase7_archive_record,
        phase7_archive_contract,
        phase7_required_import_columns,
        phase7_score_band,
        phase7_status_label,
        resolve_phase7_archive_visibility,
        seed_phase7_scorecard_archive_settings,
        validate_phase7_archive_record,
    )
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/scorecard_archive_service.py:19")
