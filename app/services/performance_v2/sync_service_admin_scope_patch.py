
"""Canlı koda doğrudan import edilmemesi gereken not modülü.

Bu dosya geçmişte sync_service.py için uygulanacak küçük bir yama notu olarak
bırakılmıştı. Python sözdizimini bozmayacak şekilde yardım fonksiyonu halinde
korunur; canlıda referans almak isteyen geliştirici bu helper'ı inceleyip gerçek
servis dosyasına kontrollü biçimde uygular.
"""
from __future__ import annotations

from typing import Any


def build_admin_scope_skip_payload(employee: Any) -> dict[str, Any]:
    return {
        "employee_id": getattr(employee, "id", None),
        "employee_name": getattr(employee, "full_name", None)
        or f"{getattr(employee, 'ad', '')} {getattr(employee, 'soyad', '')}".strip(),
        "status": "skipped",
        "skip_reason": "kapsam_disi_admin",
        "skip_message": "Sistem yöneticisi / admin performans değerlendirme kapsamı dışındadır.",
        "warnings": [],
        "infos": ["Admin kapsam dışı kullanıcı atlandı."],
        "created_assignments": 0,
        "updated_assignments": 0,
        "deleted_duplicates": 0,
    }


PATCH_NOTE = "sync_employee_assignments başında is_performance_scope_user kontrolü uygulanmalı."