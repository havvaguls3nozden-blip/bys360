from pathlib import Path

from app import create_app
from app.digital_archive.security_contract import (
    DIGITAL_ARCHIVE_WRITE_ENABLED,
    DIGITAL_ARCHIVE_WRITE_OPERATIONS,
    get_digital_archive_field_whitelist,
    get_digital_archive_write_operations,
    get_digital_archive_write_security_requirements,
)


ROOT = Path.cwd()

MODULE = ROOT / "app" / "digital_archive" / "security_contract.py"
DOC = ROOT / "docs" / "digital_archive" / "DA6B_WRITE_SECURITY_ARCHITECTURE.md"
ROUTES = ROOT / "app" / "digital_archive" / "routes.py"

TARGET_GET_ROUTES = [
    "/digital-archive/categories/new",
    "/digital-archive/physical-locations/new",
    "/digital-archive/retention-policies/new",
]

EXPECTED_OPERATIONS = {
    "category_create": "digital_archive_categories",
    "physical_location_create": "digital_archive_physical_locations",
    "retention_policy_create": "digital_archive_retention_policies",
}

errors = []

for path in [MODULE, DOC, ROUTES]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

module_text = MODULE.read_text(encoding="utf-8-sig") if MODULE.exists() else ""
doc_text = DOC.read_text(encoding="utf-8-sig") if DOC.exists() else ""
routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""

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
    if forbidden in module_text:
        errors.append(f"security_contract.py içinde yazma izi bulundu: {forbidden}")

if DIGITAL_ARCHIVE_WRITE_ENABLED is not False:
    errors.append("DIGITAL_ARCHIVE_WRITE_ENABLED False değil.")

operations = get_digital_archive_write_operations()

for key, table_name in EXPECTED_OPERATIONS.items():
    operation = operations.get(key)
    if operation is None:
        errors.append(f"Beklenen operasyon yok: {key}")
        continue

    if operation.table_name != table_name:
        errors.append(f"{key} tablo adı yanlış: {operation.table_name}")

    if not operation.required_permission.startswith("digital_archive."):
        errors.append(f"{key} yetki anahtarı beklenen formatta değil.")

    if not operation.audit_action.startswith("digital_archive."):
        errors.append(f"{key} audit action beklenen formatta değil.")

    if not operation.csrf_required:
        errors.append(f"{key} csrf_required False olmamalı.")

    if not operation.transaction_required:
        errors.append(f"{key} transaction_required False olmamalı.")

    if not operation.whitelist_required:
        errors.append(f"{key} whitelist_required False olmamalı.")

    whitelist = get_digital_archive_field_whitelist(key)
    if not whitelist:
        errors.append(f"{key} whitelist boş.")

requirements = get_digital_archive_write_security_requirements()

for token in [
    "route_level_permission_check",
    "csrf_validation",
    "server_side_validation",
    "field_whitelist",
    "audit_event",
    "transaction_rollback",
    "soft_delete_policy",
    "pre_deploy_backup",
]:
    if token not in requirements:
        errors.append(f"Güvenlik gereksinimi eksik: {token}")

for token in [
    "DIGITAL_ARCHIVE_WRITE_ENABLED = False",
    "DigitalArchiveWriteOperation",
    "DIGITAL_ARCHIVE_FIELD_WHITELISTS",
    "DIGITAL_ARCHIVE_WRITE_SECURITY_REQUIREMENTS",
]:
    if token not in module_text:
        errors.append(f"security_contract.py içinde beklenen ifade yok: {token}")

for token in [
    "Route seviyesinde yetki kontrolü",
    "CSRF doğrulaması",
    "Sunucu tarafı validasyon",
    "Alan whitelist kontrolü",
    "Audit event üretimi",
    "Transaction / rollback standardı",
    "POST açmaz ve DB yazmaz",
]:
    if token not in doc_text:
        errors.append(f"DA6B dokümanında beklenen ifade yok: {token}")

app = create_app()
app.config["TESTING"] = True
app.config["LOGIN_DISABLED"] = True
app.config["DIGITAL_ARCHIVE_ENABLED"] = True

with app.app_context():
    route_methods = {}

    for rule in app.url_map.iter_rules():
        rule_text = str(rule.rule)
        if rule_text.startswith("/digital-archive"):
            route_methods[rule_text] = sorted(
                method for method in rule.methods if method not in {"HEAD", "OPTIONS"}
            )

    for route in TARGET_GET_ROUTES:
        methods = route_methods.get(route)
        if methods != ["GET"]:
            errors.append(f"{route} yalnızca GET değil: {methods}")

    post_routes = [
        route for route, methods in route_methods.items()
        if "POST" in methods
    ]

    if post_routes:
        errors.append(f"Dijital Arşiv içinde POST route bulundu: {post_routes}")

if errors:
    raise SystemExit("DA-6B CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-6B yazma güvenliği mimari iskeleti kontrolü geçti.")
print("WRITE_ENABLED=", DIGITAL_ARCHIVE_WRITE_ENABLED)
print("OPERATION_COUNT=", len(DIGITAL_ARCHIVE_WRITE_OPERATIONS))
print("SONUC=DA6B_WRITE_SECURITY_ARCHITECTURE_OK")
