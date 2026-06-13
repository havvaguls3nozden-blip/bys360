# app/services/performance/common.py
# Mevcut dosyaya eklenebilir.

EXCLUDED_PERFORMANCE_ROLES = {
    "admin",
    "system_admin",
    "sistem_yoneticisi",
    "superadmin",
    "super_admin",
}

EXCLUDED_PERFORMANCE_ROLE_LABELS = {
    "admin",
    "sistem yöneticisi",
    "system admin",
    "super admin",
    "superadmin",
}

def _norm_text(value):
    return str(value or "").strip().lower()

def is_performance_scope_user(user) -> bool:
    """Admin / sistem yöneticisi / servis hesabı kullanıcılarını değerlendirme kapsamı dışında tut."""
    if not user:
        return False

    role = _norm_text(getattr(user, "role", ""))
    role_label = _norm_text(getattr(user, "role_label", ""))
    sicil_no = _norm_text(getattr(user, "sicil_no", ""))
    email = _norm_text(getattr(user, "email", ""))

    if role in EXCLUDED_PERFORMANCE_ROLES:
        return False
    if role_label in EXCLUDED_PERFORMANCE_ROLE_LABELS:
        return False

    # Ek güvenlik: belirgin servis / sistem hesapları
    if email.startswith("admin@") or email.startswith("system@"):
        return False
    if sicil_no in {"admin", "system", "sysadmin"}:
        return False

    if hasattr(user, "is_active") and not bool(getattr(user, "is_active", True)):
        return False

    return True