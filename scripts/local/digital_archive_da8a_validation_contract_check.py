from pathlib import Path

from app.digital_archive.validation_contract import validate_digital_archive_payload


ROOT = Path.cwd()

VALIDATION = ROOT / "app" / "digital_archive" / "validation_contract.py"
ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
DOC = ROOT / "docs" / "digital_archive" / "DA8A_VALIDATION_CONTRACT.md"

errors = []

for path in [VALIDATION, ROUTES, DOC]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

validation_text = VALIDATION.read_text(encoding="utf-8-sig") if VALIDATION.exists() else ""
routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
doc_text = DOC.read_text(encoding="utf-8-sig") if DOC.exists() else ""

for forbidden in [
    "@digital_archive_bp.post",
    "methods=[\"POST\"]",
    "methods=['POST']",
    "request.form",
    "request.get_json",
    "db.session.add",
    "db.session.merge",
    "db.session.delete",
    "db.session.commit",
]:
    if forbidden in routes_text:
        errors.append(f"routes.py içinde yazma izi bulundu: {forbidden}")
    if forbidden in validation_text:
        errors.append(f"validation_contract.py içinde yazma/request izi bulundu: {forbidden}")

for token in [
    "DigitalArchiveValidationResult",
    "DIGITAL_ARCHIVE_REQUIRED_FIELDS",
    "DIGITAL_ARCHIVE_MAX_LENGTHS",
    "DIGITAL_ARCHIVE_BOOLEAN_FIELDS",
    "DIGITAL_ARCHIVE_INTEGER_FIELDS",
    "validate_digital_archive_payload",
]:
    if token not in validation_text:
        errors.append(f"validation_contract.py içinde beklenen ifade yok: {token}")

valid_category = validate_digital_archive_payload(
    "category_create",
    {
        "parent_id": "",
        "code": "  GENEL  ",
        "name": " Genel Arşiv ",
        "description": " Açıklama ",
        "is_active": "on",
        "sort_order": "10",
    },
)

if not valid_category.is_valid:
    errors.append(f"category_create geçerli örnek hatalı döndü: {valid_category.errors}")

if valid_category.cleaned_data.get("code") != "GENEL":
    errors.append("category_create code trim edilmedi.")

if valid_category.cleaned_data.get("is_active") is not True:
    errors.append("category_create is_active boolean normalize edilmedi.")

invalid_category = validate_digital_archive_payload(
    "category_create",
    {
        "name": "",
        "title": "DB'de yok",
    },
)

if invalid_category.is_valid:
    errors.append("category_create geçersiz örnek valid döndü.")

if not any("Whitelist dışı alan" in error for error in invalid_category.errors):
    errors.append("category_create whitelist dışı alan hatası üretmedi.")

valid_location = validate_digital_archive_payload(
    "physical_location_create",
    {
        "archive_room": " Arşiv Odası 1 ",
        "cabinet_no": "A",
        "shelf_no": "1",
        "box_no": "2",
        "folder_no": "3",
        "file_no": "4",
        "physical_status": "aktif",
    },
)

if not valid_location.is_valid:
    errors.append(f"physical_location_create geçerli örnek hatalı döndü: {valid_location.errors}")

invalid_location = validate_digital_archive_payload(
    "physical_location_create",
    {
        "archive_room": "",
    },
)

if invalid_location.is_valid:
    errors.append("physical_location_create zorunlu alan boşken valid döndü.")

valid_retention = validate_digital_archive_payload(
    "retention_policy_create",
    {
        "name": " 10 Yıl Saklama ",
        "retention_years": "10",
        "action": "archive",
        "requires_approval": "true",
        "description": "",
        "is_active": "1",
    },
)

if not valid_retention.is_valid:
    errors.append(f"retention_policy_create geçerli örnek hatalı döndü: {valid_retention.errors}")

if valid_retention.cleaned_data.get("retention_years") != 10:
    errors.append("retention_policy_create retention_years integer normalize edilmedi.")

invalid_retention = validate_digital_archive_payload(
    "retention_policy_create",
    {
        "name": "Hatalı",
        "retention_years": "-1",
        "action": "archive",
    },
)

if invalid_retention.is_valid:
    errors.append("retention_policy_create negatif yıl valid döndü.")

unknown = validate_digital_archive_payload("unknown_operation", {})
if unknown.is_valid:
    errors.append("Bilinmeyen operasyon valid döndü.")

for token in [
    "DA-8A",
    "POST yoktur",
    "DB yazma yoktur",
    "Whitelist dışı alanlar reddedilir",
    "retention_years negatif olamaz",
]:
    if token not in doc_text:
        errors.append(f"DA8A dokümanında beklenen ifade yok: {token}")

if errors:
    raise SystemExit("DA-8A CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-8A server-side validation contract kontrolü geçti.")
print("SONUC=DA8A_VALIDATION_CONTRACT_OK")
