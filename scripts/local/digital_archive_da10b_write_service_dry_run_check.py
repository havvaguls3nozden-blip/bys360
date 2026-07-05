from pathlib import Path

from app import create_app
from app.digital_archive.security_contract import (
    digital_archive_write_is_enabled,
    get_digital_archive_write_operations,
)
from app.digital_archive.security_integration_contract import (
    digital_archive_security_contract_allows_write,
    digital_archive_security_integration_is_enabled,
)
from app.digital_archive.write_service import (
    DIGITAL_ARCHIVE_WRITE_SERVICE_MODE,
    DIGITAL_ARCHIVE_WRITE_SERVICE_VERSION,
    build_digital_archive_write_intent,
)


ROOT = Path.cwd()

SERVICE = ROOT / "app" / "digital_archive" / "write_service.py"
ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
DOC = ROOT / "docs" / "digital_archive" / "DA10B_WRITE_SERVICE_DRY_RUN_CONTRACT.md"

errors = []

for path in [SERVICE, ROUTES, DOC]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

service_text = SERVICE.read_text(encoding="utf-8-sig") if SERVICE.exists() else ""
routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
doc_text = DOC.read_text(encoding="utf-8-sig") if DOC.exists() else ""

for forbidden in [
    "db.session",
    "session.add",
    "session.merge",
    "session.delete",
    "session.commit",
    "session.flush",
    "request.form",
    "request.get_json",
    "@digital_archive_bp.post",
    "methods=[\"POST\"]",
    "methods=['POST']",
]:
    if forbidden in service_text:
        errors.append(f"write_service.py içinde yasaklı yazma/request izi bulundu: {forbidden}")

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

if DIGITAL_ARCHIVE_WRITE_SERVICE_MODE != "DRY_RUN":
    errors.append("Write service mode DRY_RUN değil.")

if DIGITAL_ARCHIVE_WRITE_SERVICE_VERSION != "DA-10B":
    errors.append("Write service version DA-10B değil.")

if digital_archive_write_is_enabled() is not False:
    errors.append("DIGITAL_ARCHIVE_WRITE_ENABLED False değil.")

if digital_archive_security_integration_is_enabled() is not False:
    errors.append("DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED False değil.")

if digital_archive_security_contract_allows_write() is not False:
    errors.append("WRITE_ALLOWED False değil.")

samples = {
    "category_create": {
        "parent_id": "",
        "code": "GENEL",
        "name": "Genel Arşiv",
        "description": "",
        "is_active": "true",
        "sort_order": "1",
        "unexpected_field": "reddedilmeli",
    },
    "physical_location_create": {
        "archive_room": "Arşiv Odası",
        "cabinet_no": "A",
        "shelf_no": "1",
        "box_no": "1",
        "folder_no": "1",
        "file_no": "1",
        "physical_status": "aktif",
        "unexpected_field": "reddedilmeli",
    },
    "retention_policy_create": {
        "name": "10 Yıl",
        "retention_years": "10",
        "action": "archive",
        "requires_approval": "true",
        "description": "",
        "is_active": "true",
        "unexpected_field": "reddedilmeli",
    },
}

operations = get_digital_archive_write_operations()

if set(samples.keys()) != set(operations.keys()):
    errors.append(f"Sample operasyonları write operasyonlarıyla uyumlu değil. samples={sorted(samples.keys())}, operations={sorted(operations.keys())}")

for operation_key, sample in samples.items():
    intent = build_digital_archive_write_intent(operation_key, sample, user_id=1)

    if intent.operation_key != operation_key:
        errors.append(f"{operation_key} intent operation_key uyumsuz.")

    if not intent.table_name:
        errors.append(f"{operation_key} intent table_name boş.")

    if not intent.draft_route:
        errors.append(f"{operation_key} intent draft_route boş.")

    if intent.is_valid is not True:
        errors.append(f"{operation_key} geçerli sample valid değil: {intent.validation_errors}")

    if intent.write_allowed is not False:
        errors.append(f"{operation_key} dry-run aşamasında write_allowed False değil.")

    if "write_disabled" not in intent.guard_reasons:
        errors.append(f"{operation_key} guard_reasons içinde write_disabled yok: {intent.guard_reasons}")

    if "unexpected_field" not in intent.rejected_fields:
        errors.append(f"{operation_key} whitelist dışı alan reddedilmedi.")

    if "unexpected_field" in intent.payload:
        errors.append(f"{operation_key} whitelist dışı alan payload içinde kaldı.")

unknown_intent = build_digital_archive_write_intent("unknown_operation", {"name": "X"}, user_id=1)

if unknown_intent.is_valid is not False:
    errors.append("unknown_operation valid görünüyor.")

if "unknown_operation" not in unknown_intent.guard_reasons:
    errors.append("unknown_operation guard reason yok.")

if "write_disabled" not in unknown_intent.guard_reasons:
    errors.append("unknown_operation için write_disabled guard reason yok.")

app = create_app()
app.config["TESTING"] = True
app.config["LOGIN_DISABLED"] = True
app.config["DIGITAL_ARCHIVE_ENABLED"] = True

with app.app_context():
    post_routes = []

    for rule in app.url_map.iter_rules():
        rule_text = str(rule.rule)

        if not rule_text.startswith("/digital-archive"):
            continue

        methods = sorted(method for method in rule.methods if method not in {"HEAD", "OPTIONS"})

        if "POST" in methods:
            post_routes.append(rule_text)

    if post_routes:
        errors.append(f"Dijital Arşiv içinde POST route bulundu: {post_routes}")

for token in [
    "DA-10B",
    "write_service.py",
    "DRY_RUN",
    "POST route açılmamıştır",
    "DB yazma yapılmamıştır",
    "Canlı ortamda işlem yapılmamıştır",
]:
    if token not in doc_text:
        errors.append(f"DA10B dokümanında beklenen ifade yok: {token}")

if errors:
    raise SystemExit("DA-10B CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-10B write service dry-run contract kontrolü geçti.")
print("POST_ROUTE_COUNT=", len(post_routes))
print("WRITE_OPERATION_COUNT=", len(operations))
print("WRITE_ALLOWED=", digital_archive_security_contract_allows_write())
print("SONUC=DA10B_WRITE_SERVICE_DRY_RUN_CONTRACT_OK")
