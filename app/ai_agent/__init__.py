
"""BYS360 AG-1 BYS360 Asistanı modülü.

Bu modül, BYS360 Asistanı ve AI Karar Destek çizgisini bozmadan,
yetki kontrollü özet, güvenli yönlendirme ve işlem önerisi omurgası sağlar.
AG-1 aşamasında dış AI servisi çağrısı ve otomatik veri değiştirme yoktur.
"""
from __future__ import annotations

try:
    from .routes import ai_agent_bp
except Exception:  # Uygulama başlangıcını kırmamak için güvenli fallback.
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/ai_agent/__init__.py:12")
    ai_agent_bp = None

__all__ = ["ai_agent_bp"]
