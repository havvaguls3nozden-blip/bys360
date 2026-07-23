"""Geriye dönük uyumluluk shim.

Bu dosya taşınmadan önce app.security_headers olarak import ediliyordu.
Yeni konumu: app.security.headers
Lütfen import yollarını güncelleyin; bu shim bakım modunda kalacak.
"""
from __future__ import annotations

from app.security.headers import (  # noqa: F401
    DEFAULT_CSP,
    apply_default_security_headers,
    build_csp_header,
)
