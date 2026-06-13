
"""Performans mail/export helper ailesi.

Geriye uyumluluk notu:
- Faz D ile Excel uretimi app.services.performance.export_service altina tasindi.
- Eski importlari kirmamak icin bu dosya ayni ismi yeniden disariya acar.
"""
from __future__ import annotations

from app.services.performance.export_service import build_styled_excel_bytes

__all__ = ["build_styled_excel_bytes"]