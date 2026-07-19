"""
A10Q_COMPATIBILITY_WRAPPER

Bu dosya BYS360 A10Q teknik borç temizliği kapsamında bilerek korunmuştur.
Eski import yolunu kırmamak için yeni modüle yönlendiren compatibility wrapper'dır.

Yeni gerçek modül:
app/services/performance/common_admin_scope_maintenance.py
"""

from .common_admin_scope_maintenance import (
    EXCLUDED_PERFORMANCE_ROLES,
    EXCLUDED_PERFORMANCE_ROLE_LABELS,
    is_performance_scope_user,
)
