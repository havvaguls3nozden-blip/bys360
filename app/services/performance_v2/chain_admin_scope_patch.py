# app/services/performance_v2/chain.py
# Zincir çözümlemesi başlamadan önce kapsam dışı admin'i erken döndür.

from app.services.performance.common import is_performance_scope_user

def build_resolved_chain(employee, period=None, *args, **kwargs):
    if not is_performance_scope_user(employee):
        return {
            "employee_id": getattr(employee, "id", None),
            "employee_name": getattr(employee, "full_name", None) or f"{getattr(employee, 'ad', '')} {getattr(employee, 'soyad', '')}".strip(),
            "is_valid": False,
            "is_scope_excluded": True,
            "warning_count": 0,
            "info_count": 1,
            "warnings": [],
            "infos": ["Admin kullanıcı performans zinciri kapsamı dışındadır."],
            "manager_level_1": None,
            "manager_level_2": None,
            "manager_level_3": None,
        }

    # mevcut build_resolved_chain gövdesi burada devam eder