"""Geriye dönük uyumluluk shim.

Bu dosya taşınmadan önce app.security_audit olarak import ediliyordu.
Yeni konumu: app.security.audit
Lütfen import yollarını güncelleyin; bu shim bakım modunda kalacak.
"""
from __future__ import annotations

from app.security.audit import (  # noqa: F401
    SecurityAuditFinding,
    collect_runtime_security_findings,
    findings_to_dicts,
    build_security_audit_summary,
    log_runtime_security_posture,
)
