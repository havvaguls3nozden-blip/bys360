"""Geriye dönük uyumluluk shim.

Bu dosya taşınmadan önce app.security_guards olarak import ediliyordu.
Yeni konumu: app.security.guards
Lütfen import yollarını güncelleyin; bu shim bakım modunda kalacak.
"""
from __future__ import annotations

from app.security.guards import (  # noqa: F401
    UploadGuardProfile,
    DEFAULT_UPLOAD_PROFILES,
    resolve_upload_guard,
    build_security_runtime_report,
)
