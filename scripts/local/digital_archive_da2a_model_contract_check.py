from pathlib import Path
import py_compile

from app.digital_archive.model_contract import (
    DIGITAL_ARCHIVE_TABLE_CONTRACTS,
    DIGITAL_ARCHIVE_TABLE_PREFIX,
    DOCUMENT_CONFIDENTIALITY_VALUES,
    DOCUMENT_STATUS_VALUES,
    ENTITY_LINK_TYPES,
    PHYSICAL_DOCUMENT_STATUS_VALUES,
    RETENTION_ACTION_VALUES,
    get_digital_archive_table_names,
    validate_digital_archive_contracts,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "app" / "digital_archive" / "model_contract.py"

py_compile.compile(str(CONTRACT_PATH), doraise=True)

errors = validate_digital_archive_contracts()
if errors:
    raise SystemExit("DA-2A model sözleşmesi hatalı:\n" + "\n".join(errors))

table_names = get_digital_archive_table_names()

if len(table_names) < 8:
    raise SystemExit("DA-2A FAIL: Beklenen digital_archive tablo ailesi eksik.")

for table_name in table_names:
    if not table_name.startswith(DIGITAL_ARCHIVE_TABLE_PREFIX):
        raise SystemExit(f"DA-2A FAIL: Prefix hatası: {table_name}")

required_tables = {
    "digital_archive_categories",
    "digital_archive_documents",
    "digital_archive_document_versions",
    "digital_archive_physical_locations",
    "digital_archive_retention_policies",
    "digital_archive_access_rules",
    "digital_archive_audit_events",
    "digital_archive_entity_links",
    "digital_archive_ocr_jobs",
}

missing_tables = sorted(required_tables.difference(table_names))
if missing_tables:
    raise SystemExit("DA-2A FAIL: Eksik tablolar:\n" + "\n".join(missing_tables))

if "confidential" not in DOCUMENT_CONFIDENTIALITY_VALUES:
    raise SystemExit("DA-2A FAIL: confidential gizlilik değeri eksik.")

if "destroyed" not in DOCUMENT_STATUS_VALUES:
    raise SystemExit("DA-2A FAIL: destroyed belge statüsü eksik.")

if "damaged" not in PHYSICAL_DOCUMENT_STATUS_VALUES:
    raise SystemExit("DA-2A FAIL: damaged fiziksel durum değeri eksik.")

if "destroy_with_approval" not in RETENTION_ACTION_VALUES:
    raise SystemExit("DA-2A FAIL: onaylı imha aksiyonu eksik.")

for expected_link in ("personnel", "performance", "support_ticket", "file_center", "location", "parcel", "media"):
    if expected_link not in ENTITY_LINK_TYPES:
        raise SystemExit(f"DA-2A FAIL: entity link tipi eksik: {expected_link}")

for contract in DIGITAL_ARCHIVE_TABLE_CONTRACTS:
    if contract.table_name == "digital_archive_documents":
        required_document_fields = {
            "document_no",
            "title",
            "document_type",
            "category_id",
            "confidentiality_level",
            "physical_location_id",
            "retention_policy_id",
        }
        missing_fields = required_document_fields.difference(contract.required_fields)
        if missing_fields:
            raise SystemExit(
                "DA-2A FAIL: digital_archive_documents alanları eksik:\n"
                + "\n".join(sorted(missing_fields))
            )

print("OK: DA-2A Dijital Arşiv model sözleşmesi geçti.")
print("TABLES:")
for table_name in table_names:
    print(f"- {table_name}")
