from pathlib import Path

from app import create_app
from app.digital_archive.security_contract import (
    digital_archive_write_is_enabled,
    get_digital_archive_write_operations,
)
from app.digital_archive.security_integration_contract import (
    DIGITAL_ARCHIVE_SECURITY_CONTRACT_VERSION,
    digital_archive_security_contract_allows_write,
    digital_archive_security_integration_is_enabled,
    get_digital_archive_integration_candidate_modules,
    get_digital_archive_operation_security_profile,
    get_digital_archive_operation_security_profiles,
    get_digital_archive_security_decision_order,
    get_digital_archive_security_requirements,
)


ROOT = Path.cwd()

CONTRACT = ROOT / "app" / "digital_archive" / "security_integration_contract.py"
ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
DOC = ROOT / "docs" / "digital_archive" / "DA9C_SECURITY_INTEGRATION_CONTRACT.md"

errors = []

for path in [CONTRACT, ROUTES, DOC]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

contract_text = CONTRACT.read_text(encoding="utf-8-sig") if CONTRACT.exists() else ""
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
    if forbidden in contract_text:
        errors.append(f"security_integration_contract.py içinde yazma/request izi bulundu: {forbidden}")

if DIGITAL_ARCHIVE_SECURITY_CONTRACT_VERSION != "DA-9C":
    errors.append("Security contract version DA-9C değil.")

if digital_archive_write_is_enabled() is not False:
    errors.append("DIGITAL_ARCHIVE_WRITE_ENABLED False değil.")

if digital_archive_security_integration_is_enabled() is not False:
    errors.append("DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED False değil.")

if digital_archive_security_contract_allows_write() is not False:
    errors.append("security contract yazmaya izin veriyor görünüyor.")

requirements = get_digital_archive_security_requirements()
required_requirement_keys = {
    "authentication",
    "route_permission",
    "csrf",
    "payload_validation",
    "field_whitelist",
    "audit_event",
    "transaction",
    "feature_flag",
    "failure_handling",
}

missing_requirement_keys = sorted(required_requirement_keys - set(requirements.keys()))
if missing_requirement_keys:
    errors.append(f"Eksik güvenlik gereksinimleri: {missing_requirement_keys}")

decision_order = get_digital_archive_security_decision_order()
if tuple(decision_order) != (
    "authentication",
    "route_permission",
    "csrf",
    "feature_flag",
    "field_whitelist",
    "payload_validation",
    "transaction",
    "audit_event",
    "failure_handling",
):
    errors.append(f"Güvenlik karar sırası beklenenle uyumlu değil: {decision_order}")

for key, requirement in requirements.items():
    if requirement.mandatory is not True:
        errors.append(f"Güvenlik gereksinimi mandatory değil: {key}")

    if not requirement.candidate_modules:
        errors.append(f"Güvenlik gereksinimi candidate module içermiyor: {key}")

profiles = get_digital_archive_operation_security_profiles()
operations = get_digital_archive_write_operations()

if set(profiles.keys()) != set(operations.keys()):
    errors.append(f"Profil anahtarları operasyonlarla uyumlu değil. profiles={sorted(profiles.keys())}, operations={sorted(operations.keys())}")

for operation_key, operation in operations.items():
    profile = get_digital_archive_operation_security_profile(operation_key)

    if profile is None:
        errors.append(f"Operasyon profili yok: {operation_key}")
        continue

    if profile.required_permission != operation.required_permission:
        errors.append(f"{operation_key} required_permission uyumsuz.")

    if profile.audit_action != operation.audit_action:
        errors.append(f"{operation_key} audit_action uyumsuz.")

    checks = {
        "authentication_required": profile.authentication_required,
        "route_permission_required": profile.route_permission_required,
        "csrf_required": profile.csrf_required,
        "payload_validation_required": profile.payload_validation_required,
        "field_whitelist_required": profile.field_whitelist_required,
        "audit_required": profile.audit_required,
        "transaction_required": profile.transaction_required,
        "feature_flag_guard_required": profile.feature_flag_guard_required,
    }

    for check_name, value in checks.items():
        if value is not True:
            errors.append(f"{operation_key} için {check_name} True değil.")

candidate_modules = get_digital_archive_integration_candidate_modules()
for category in ["authentication", "permission", "csrf", "audit", "transaction_example"]:
    modules = candidate_modules.get(category, ())
    if not modules:
        errors.append(f"Candidate module kategorisi boş: {category}")

    for module in modules:
        module_path = ROOT / module
        if not module_path.exists():
            errors.append(f"Candidate module dosyası yok: {module}")

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
    "DA-9C",
    "security_integration_contract.py",
    "Oturum doğrulaması",
    "Route seviyesinde yetki kontrolü",
    "CSRF doğrulaması",
    "Audit ve güvenlik izi",
    "POST yoktur",
    "DB yazma yoktur",
    "Canlıya işlem yapılmamıştır",
]:
    if token not in doc_text:
        errors.append(f"DA9C dokümanında beklenen ifade yok: {token}")

if errors:
    raise SystemExit("DA-9C CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-9C security integration contract kontrolü geçti.")
print("POST_ROUTE_COUNT=", len(post_routes))
print("OPERATION_PROFILE_COUNT=", len(profiles))
print("REQUIREMENT_COUNT=", len(requirements))
print("WRITE_ALLOWED=", digital_archive_security_contract_allows_write())
print("SONUC=DA9C_SECURITY_INTEGRATION_CONTRACT_OK")
