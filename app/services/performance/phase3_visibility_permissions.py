
"""Geriye uyum alias dosyası.

Faz 3.1 rol matrisi ana servis dosyası: app/services/performance/phase3_role_matrix.py
Bu alias, önceki/sonraki Faz 3 yamalarının eski servis adını araması halinde kırılmayı önler.
"""
from __future__ import annotations

from app.services.performance.phase3_role_matrix import (
    BYS360_PHASE3_1_ROLE_MATRIX_MARKER,
    BYS360_PHASE3_1_ROLE_MATRIX_VERSION,
    GENERAL_VIEW_ROLE_KEYS,
    PERSONNEL_ROLE_KEYS,
    PHASE3_ACCESS_DENIED_MESSAGE,
    ROLE_ALIASES,
    ROLE_PRIORITY,
    ROLE_VISIBILITY_MATRIX,
    SCOPED_MANAGER_ROLE_KEYS,
    TECHNICAL_MANAGEMENT_ROLE_KEYS,
    Any,
    get_phase3_role_matrix,
    get_phase3_visibility_profile,
    normalize_role_value,
    phase3_can_view_general,
    phase3_can_view_technical_management,
    phase3_denied_message,
    phase3_requires_own_record_only,
    phase3_requires_scope_filter,
    phase3_role_matrix_summary,
    resolve_phase3_role_key,
)
