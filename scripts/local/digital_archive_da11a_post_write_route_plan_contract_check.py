from pathlib import Path

from app import create_app
from app.digital_archive.security_contract import (
    digital_archive_write_is_enabled,
    get_digital_archive_write_operations,
)
from app.digital_archive.security_integration_contract import (
    digital_archive_security_contract_allows_write,
    digital_archive_security_integration_is_enabled,
    get_digital_archive_operation_security_profiles,
    get_digital_archive_security_decision_order,
    get_digital_archive_security_requirements,
)
from app.digital_archive.write_service import (
    DIGITAL_ARCHIVE_WRITE_SERVICE_MODE,
    DIGITAL_ARCHIVE_WRITE_SERVICE_VERSION,
)


ROOT = Path.cwd()

DOC = ROOT / "docs" / "digital_archive" / "DA11A_POST_WRITE_ROUTE_PLAN_CONTRACT.md"
ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
SERVICE = ROOT / "app" / "digital_archive" / "write_service.py"

errors = []

for path in [DOC, ROUTES, SERVICE]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

doc_text = DOC.read_text(encoding="utf-8-sig") if DOC.exists() else ""
routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
service_text = SERVICE.read_text(encoding="utf-8-sig") if SERVICE.exists() else ""

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
        errors.append(f"routes.py içinde henüz açılmaması gereken yazma izi bulundu: {forbidden}")

for forbidden in [
    "db.session",
    "session.add",
    "session.merge",
    "session.delete",
    "session.commit",
    "session.flush",
    "request.form",
    "request.get_json",
]:
    if forbidden in service_text:
        errors.append(f"write_service.py içinde yasaklı yazma/request izi bulundu: {forbidden}")

if digital_archive_write_is_enabled() is not False:
    errors.append("DIGITAL_ARCHIVE_WRITE_ENABLED False değil.")

if digital_archive_security_integration_is_enabled() is not False:
    errors.append("DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED False değil.")

if digital_archive_security_contract_allows_write() is not False:
    errors.append("WRITE_ALLOWED False değil.")

if DIGITAL_ARCHIVE_WRITE_SERVICE_MODE != "DRY_RUN":
    errors.append("Write service mode DRY_RUN değil.")

if DIGITAL_ARCHIVE_WRITE_SERVICE_VERSION != "DA-10B":
    errors.append("Write service version DA-10B değil.")

operations = get_digital_archive_write_operations()
profiles = get_digital_archive_operation_security_profiles()
requirements = get_digital_archive_security_requirements()
decision_order = tuple(get_digital_archive_security_decision_order())

if len(operations) != 3:
    errors.append(f"Write operation count 3 değil: {len(operations)}")

if len(profiles) != 3:
    errors.append(f"Operation profile count 3 değil: {len(profiles)}")

if len(requirements) != 9:
    errors.append(f"Security requirement count 9 değil: {len(requirements)}")

expected_decision_order = (
    "authentication",
    "route_permission",
    "csrf",
    "feature_flag",
    "field_whitelist",
    "payload_validation",
    "transaction",
    "audit_event",
    "failure_handling",
)

if decision_order != expected_decision_order:
    errors.append(f"Security decision order uyumsuz: {decision_order}")

planned_routes = {
    "category_create": {
        "draft": "/digital-archive/categories/new",
        "post": "/digital-archive/categories",
        "table": "digital_archive_categories",
    },
    "physical_location_create": {
        "draft": "/digital-archive/physical-locations/new",
        "post": "/digital-archive/physical-locations",
        "table": "digital_archive_physical_locations",
    },
    "retention_policy_create": {
        "draft": "/digital-archive/retention-policies/new",
        "post": "/digital-archive/retention-policies",
        "table": "digital_archive_retention_policies",
    },
}

for operation_key, expected in planned_routes.items():
    operation = operations.get(operation_key)
    profile = profiles.get(operation_key)

    if operation is None:
        errors.append(f"Operation yok: {operation_key}")
        continue

    if profile is None:
        errors.append(f"Security profile yok: {operation_key}")
        continue

    if operation.table_name != expected["table"]:
        errors.append(f"{operation_key} tablo uyumsuz: {operation.table_name}")

    if operation.draft_route != expected["draft"]:
        errors.append(f"{operation_key} draft route uyumsuz: {operation.draft_route}")

    for token in [operation_key, expected["draft"], expected["post"], expected["table"]]:
        if token not in doc_text:
            errors.append(f"DA11A dokümanında beklenen ifade yok: {token}")

for token in [
    "DA-11A",
    "POST route açılmamıştır",
    "DB yazma yapılmamıştır",
    "Canlı ortamda işlem yapılmamıştır",
    "Authentication",
    "Route permission",
    "CSRF",
    "Feature flag",
    "Field whitelist",
    "Payload validation",
    "Transaction",
    "Audit event",
    "Failure handling",
    "rollback",
]:
    if token not in doc_text:
        errors.append(f"DA11A dokümanında beklenen ifade yok: {token}")

app = create_app()
app.config["TESTING"] = True
app.config["LOGIN_DISABLED"] = True
app.config["DIGITAL_ARCHIVE_ENABLED"] = True

with app.app_context():
    post_routes = []
    route_methods = {}

    for rule in app.url_map.iter_rules():
        rule_text = str(rule.rule)

        if not rule_text.startswith("/digital-archive"):
            continue

        methods = sorted(method for method in rule.methods if method not in {"HEAD", "OPTIONS"})
        route_methods[rule_text] = methods

        if "POST" in methods:
            post_routes.append(rule_text)

    if post_routes:
        errors.append(f"Dijital Arşiv içinde POST route bulundu: {post_routes}")

if errors:
    raise SystemExit("DA-11A CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-11A POST write route plan contract kontrolü geçti.")
print("POST_ROUTE_COUNT=", len(post_routes))
print("WRITE_OPERATION_COUNT=", len(operations))
print("OPERATION_PROFILE_COUNT=", len(profiles))
print("SECURITY_REQUIREMENT_COUNT=", len(requirements))
print("WRITE_ALLOWED=", digital_archive_security_contract_allows_write())
print("SONUC=DA11A_POST_WRITE_ROUTE_PLAN_CONTRACT_OK")
