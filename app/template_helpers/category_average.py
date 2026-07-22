
"""Kategori ortalaması template yardımcıları.

BYS360_MAINTENANCE_V13_P1_TEMPLATE_HELPERS
"""
from __future__ import annotations

from flask import Flask


def register_category_average_helpers(app: Flask) -> None:
    """Karne şablonları için kişi detayı göstermeyen kategori ortalaması yardımcıları."""
    if getattr(app, "_bys360_phase2_5_category_average_helpers_registered", False):
        return

    @app.context_processor
    def _bys360_phase2_5_category_average_context() -> dict[str, object]:
        def _for_evaluation(evaluation: object) -> dict[str, object]:
            try:
                from app.services.performance.category_stats import (
                    build_category_average_for_evaluation,
                )
                return build_category_average_for_evaluation(evaluation)
            except Exception:
                app.logger.exception("Kategori ortalaması değerlendirme yardımcısı güvenli varsayılana düştü.")
                return {"enabled": False, "category_label": "Diğer", "average_score": 0.0, "count": 0, "detail_visible": False, "person_detail_visible": False, "privacy_note": "Kategori ortalaması kişi detayı göstermeden hesaplanır."}

        def _for_user(user: object, period_id: int | None = None) -> dict[str, object]:
            try:
                from app.services.performance.category_stats import build_category_average_for_user
                return build_category_average_for_user(user, period_id=period_id)
            except Exception:
                app.logger.exception("Kategori ortalaması kullanıcı yardımcısı güvenli varsayılana düştü.")
                return {"enabled": False, "category_label": "Diğer", "average_score": 0.0, "count": 0, "detail_visible": False, "person_detail_visible": False, "privacy_note": "Kategori ortalaması kişi detayı göstermeden hesaplanır."}

        return {"bys360_category_average_for_evaluation": _for_evaluation, "bys360_category_average_for_user": _for_user}

    app._bys360_phase2_5_category_average_helpers_registered = True  # type: ignore[attr-defined]
