"""BYS360 menu registry data bridge module.

Personel rol matrisi görünürlük/temizlik sabitleri.

Bu dosya P11-D2 kapsamında app/menu_registry.py içindeki büyük ve güvenli
top-level veri bloklarını aynı içerikle taşımak için oluşturulmuştur.
menu_key değerleri ve veri içerikleri değiştirilmemelidir.
"""
from __future__ import annotations


_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_DISALLOWED_KEYS = {
    "hr_management", "hr_reports", "hr_personnel_operations", "hr_career_planning", "hr_reward_discipline",
    "personnel_dashboard", "personnel_create", "personnel_edit", "organization_unit_versions", "hierarchy",
    "leave", "attendance", "delegation", "personnel_reports",
    "personnel_requests", "personnel_validity", "personnel_assets", "personnel_checklists",
    "personnel_reminders", "personnel_lifecycle", "personnel_handover", "personnel_approvals",
    "personnel_request_analytics", "personnel_request_tasks",
}

_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS = {
    "hr_personnel_operations", "hr_career_planning", "hr_reward_discipline",
    "personnel_dashboard", "personnel_create", "personnel_edit", "organization_unit_versions", "hierarchy",
    "leave", "attendance", "delegation", "personnel_reports",
    "personnel_requests", "personnel_validity", "personnel_assets", "personnel_checklists",
    "personnel_reminders", "personnel_lifecycle", "personnel_handover", "personnel_approvals",
    "personnel_request_analytics", "personnel_request_tasks",
}
