"""Aşama 10 gelişim rehberini karne şablonlarında güvenli kullanmak için context processor."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def register_phase10_scorecard_integration(app):
    @app.context_processor
    def _phase10_scorecard_context():
        try:
            from app.performance.phase10_development_guidance_ui import (
                get_scorecard_development_guidance,
            )
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            def get_scorecard_development_guidance(*args, **kwargs):
                return []
        return {
            "get_scorecard_development_guidance": get_scorecard_development_guidance
        }
