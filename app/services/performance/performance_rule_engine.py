# -*- coding: utf-8 -*-

"""BYS360 Faz 1.3 uyumluluk köprüsü.

Asıl kural motoru kullanıcı planındaki kalıcı adreste tutulur:
``app.performance.services.performance_rule_engine``.
Bu dosya mevcut servis katmanından import etmek isteyen kodlar için köprü sağlar.
"""
from __future__ import annotations

from app.performance.services.performance_rule_engine import *  # noqa: F401,F403
