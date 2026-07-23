import logging

logger = logging.getLogger(__name__)
# BYS360 SP-1A Stratejik Performans modülü
# KPI, hedef, yetkinlik ve öz değerlendirme çekirdek katmanı.

try:
    from .routes import strategic_performance_bp
except Exception:  # Blueprint importu uygulama başlangıcını bozmasın.
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    strategic_performance_bp = None
