
"""Geriye uyumlu performans engagement route girişi.

Bu dosya artık gerçek route gövdelerini taşımaz.
Route aileleri aşağıdaki modüllere ayrılmıştır:
- engagement_publish_routes
- engagement_mail_routes
- engagement_feedback_routes

Amaç:
- 2000+ satırlık tek dosya baskısını azaltmak
- yayın / mail / geri bildirim sorumluluklarını ayırmak
- mevcut import yolunu bozmadan canlı kayıtlarını korumak
"""
from __future__ import annotations

from . import (
    engagement_feedback_routes,  # noqa: F401
    engagement_mail_routes,  # noqa: F401
    engagement_publish_routes,  # noqa: F401
)
