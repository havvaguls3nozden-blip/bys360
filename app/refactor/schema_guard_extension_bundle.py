
"""BYS360 Faz 1C schema_guard extension bundle.

Bu dosya, projede dağınık duran schema_guard snippet/hotfix parçalarını tek merkezde
okunabilir hale getiren ara konsolidasyon katmanıdır. Doğrudan mevcut
`app/schema_guard.py` dosyasını değiştirmez.

Sonraki fazda iki olası kullanım vardır:
1. İçerik satır içi eritilir.
2. `schema_guard.py` içinden kontrollü import yapılır.
"""
from __future__ import annotations

SCHEMA_GUARD_SOURCES = [
    "app/schema_guard_phase7_snippet.py",
    "app/schema_guard_phase8_snippet.py",
    "app/schema_guard_phase7_approval_hotfix_snippet.py",
    "app/schema_guard_faz81_snippet.py",
]

PHASE7_TABLES = [
    "education_video_certificate_approvals",
    "education_video_compliance_rules",
]

PHASE7_COLUMNS = [
    ("education_videos", "executive_priority"),
    ("education_videos", "mandatory_completion_days"),
]

PHASE8_TABLES = [
    "education_video_access_policies",
    "education_video_export_jobs",
    "education_video_audit_logs",
]

PHASE8_COLUMNS = [
    ("education_videos", "sensitivity_label"),
    ("education_videos", "watermark_enabled"),
]

PHASE7_APPROVAL_TABLES = [
    "education_video_approvals",
]

FAZ81_TABLES = [
    "education_video_chapters",
    "education_video_micro_exams",
    "education_video_learning_paths",
]

MERGE_PLAN = {
    "bundle_name": "schema_guard_extension_bundle",
    "strategy": "bundle_then_inline",
    "risk": "orta",
    "next_step": "Mevcut schema_guard.py içindeki TABLE_REPAIRS / COLUMN_REPAIRS yapısına kontrollü eritme.",
}