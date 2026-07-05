"""Dijital Arşiv veri modeli sözleşmesi.

DA-2A:
- Bu dosya gerçek SQLAlchemy modeli oluşturmaz.
- Migration üretmez.
- Mevcut BYS360 tablolarına dokunmaz.
- DA-2B/DA-2C aşamasında oluşturulacak digital_archive_* tablo ailesini sabitler.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DigitalArchiveTableContract:
    """Dijital Arşiv tablo sözleşmesi."""

    table_name: str
    purpose: str
    required_fields: tuple[str, ...]


DIGITAL_ARCHIVE_TABLE_PREFIX = "digital_archive_"

DOCUMENT_STATUS_VALUES = (
    "draft",
    "active",
    "archived",
    "retention_review",
    "destruction_pending",
    "destroyed",
)

DOCUMENT_CONFIDENTIALITY_VALUES = (
    "general",
    "internal",
    "unit_private",
    "personal_sensitive",
    "confidential",
)

PHYSICAL_DOCUMENT_STATUS_VALUES = (
    "original",
    "copy",
    "missing",
    "damaged",
    "external_archive",
    "destruction_pending",
)

RETENTION_ACTION_VALUES = (
    "keep",
    "review",
    "archive_permanent",
    "destroy_with_approval",
)

ENTITY_LINK_TYPES = (
    "personnel",
    "performance",
    "support_ticket",
    "message",
    "announcement",
    "survey",
    "file_center",
    "meeting",
    "project",
    "inventory",
    "location",
    "parcel",
    "media",
)

DIGITAL_ARCHIVE_TABLE_CONTRACTS = (
    DigitalArchiveTableContract(
        table_name="digital_archive_categories",
        purpose="Dosya planı, arşiv kategori ağacı ve belge sınıflandırması.",
        required_fields=(
            "id",
            "parent_id",
            "code",
            "name",
            "description",
            "is_active",
            "sort_order",
            "created_at",
            "updated_at",
        ),
    ),
    DigitalArchiveTableContract(
        table_name="digital_archive_documents",
        purpose="Belge kayıt kartı, metadata, gizlilik, birim, konu ve arşiv durumu.",
        required_fields=(
            "id",
            "document_no",
            "title",
            "document_type",
            "document_date",
            "subject",
            "category_id",
            "owner_user_id",
            "organization_unit_id",
            "related_personnel_id",
            "confidentiality_level",
            "status",
            "retention_policy_id",
            "physical_location_id",
            "tags",
            "created_at",
            "updated_at",
            "created_by_id",
            "updated_by_id",
        ),
    ),
    DigitalArchiveTableContract(
        table_name="digital_archive_document_versions",
        purpose="Belge dosyası, versiyonlama, dosya bütünlüğü ve revizyon geçmişi.",
        required_fields=(
            "id",
            "document_id",
            "version_no",
            "file_name",
            "storage_path",
            "mime_type",
            "file_size",
            "sha256_hash",
            "revision_note",
            "uploaded_by_id",
            "created_at",
        ),
    ),
    DigitalArchiveTableContract(
        table_name="digital_archive_physical_locations",
        purpose="Fiziksel arşiv odası, dolap, raf, kutu, klasör ve belge hareket bilgisi.",
        required_fields=(
            "id",
            "archive_room",
            "cabinet_no",
            "shelf_no",
            "box_no",
            "folder_no",
            "file_no",
            "physical_status",
            "delivered_to_user_id",
            "delivered_at",
            "returned_at",
            "created_at",
            "updated_at",
        ),
    ),
    DigitalArchiveTableContract(
        table_name="digital_archive_retention_policies",
        purpose="Saklama süresi, gözden geçirme, kalıcı arşiv ve imha karar altyapısı.",
        required_fields=(
            "id",
            "name",
            "retention_years",
            "action",
            "requires_approval",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ),
    ),
    DigitalArchiveTableContract(
        table_name="digital_archive_access_rules",
        purpose="Belge türü, gizlilik seviyesi, rol, birim ve kişi bazlı erişim kuralları.",
        required_fields=(
            "id",
            "document_id",
            "role_name",
            "organization_unit_id",
            "user_id",
            "can_view",
            "can_download",
            "can_update",
            "can_delete",
            "can_manage_access",
            "created_at",
            "created_by_id",
        ),
    ),
    DigitalArchiveTableContract(
        table_name="digital_archive_audit_events",
        purpose="Belge görüntüleme, indirme, güncelleme, revizyon, yetki ve imha denetim izi.",
        required_fields=(
            "id",
            "document_id",
            "event_type",
            "actor_user_id",
            "ip_address",
            "user_agent",
            "details_json",
            "created_at",
        ),
    ),
    DigitalArchiveTableContract(
        table_name="digital_archive_entity_links",
        purpose="Belgenin BYS360 personel, performans, destek, mesaj, dosya merkezi ve saha varlıklarıyla ilişkisi.",
        required_fields=(
            "id",
            "document_id",
            "entity_type",
            "entity_id",
            "relation_note",
            "created_at",
            "created_by_id",
        ),
    ),
    DigitalArchiveTableContract(
        table_name="digital_archive_ocr_jobs",
        purpose="OCR kuyruğu, iş durumu, çıkarılan metin ve arama hazırlığı.",
        required_fields=(
            "id",
            "document_version_id",
            "status",
            "extracted_text",
            "error_message",
            "started_at",
            "finished_at",
            "created_at",
        ),
    ),
)


def get_digital_archive_table_names() -> tuple[str, ...]:
    """Planlanan Dijital Arşiv tablo adlarını döndürür."""
    return tuple(contract.table_name for contract in DIGITAL_ARCHIVE_TABLE_CONTRACTS)


def validate_digital_archive_contracts() -> list[str]:
    """Sözleşme ihlallerini döndürür."""
    errors: list[str] = []
    seen: set[str] = set()

    for contract in DIGITAL_ARCHIVE_TABLE_CONTRACTS:
        if not contract.table_name.startswith(DIGITAL_ARCHIVE_TABLE_PREFIX):
            errors.append(f"Tablo prefix hatası: {contract.table_name}")

        if contract.table_name in seen:
            errors.append(f"Tekrarlanan tablo adı: {contract.table_name}")

        seen.add(contract.table_name)

        if "id" not in contract.required_fields:
            errors.append(f"id alanı eksik: {contract.table_name}")

        if "created_at" not in contract.required_fields:
            errors.append(f"created_at alanı eksik: {contract.table_name}")

        if not contract.purpose.strip():
            errors.append(f"Amaç açıklaması eksik: {contract.table_name}")

    return errors
