from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Blueprint

logger = logging.getLogger(__name__)
# BYS360 SP-1A Stratejik Performans modülü
# KPI, hedef, yetkinlik ve öz değerlendirme çekirdek katmanı.

strategic_performance_bp: Blueprint | None
try:
    from .routes import strategic_performance_bp
except Exception:  # Blueprint importu uygulama başlangıcını bozmasın.
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    strategic_performance_bp = None
