"""Dijital Arşiv model taslak alanı.

DA-1A aşamasında gerçek SQLAlchemy modeli eklenmez.
DA-1B/DA-2 aşamasında yalnızca digital_archive_* tabloları eklenecektir.
"""

PLANNED_TABLES = (
    "digital_archive_categories",
    "digital_archive_documents",
    "digital_archive_document_versions",
    "digital_archive_physical_locations",
    "digital_archive_retention_policies",
    "digital_archive_access_rules",
    "digital_archive_audit_events",
    "digital_archive_entity_links",
)
