from pathlib import Path

from app import create_app
from app.digital_archive.security_contract import digital_archive_write_is_enabled
from app.digital_archive.security_integration_contract import (
    digital_archive_security_contract_allows_write,
    digital_archive_security_integration_is_enabled,
)


ROOT = Path.cwd()

TEMPLATE = ROOT / "app" / "templates" / "digital_archive" / "passive_form.html"
ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
VALIDATION = ROOT / "app" / "digital_archive" / "validation_contract.py"
INTEGRATION = ROOT / "app" / "digital_archive" / "security_integration_contract.py"
DOC = ROOT / "docs" / "digital_archive" / "DA10A1_PASSIVE_FORM_GET_ONLY_NOTE.md"

errors = []

for path in [TEMPLATE, ROUTES, VALIDATION, INTEGRATION, DOC]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

template_text = TEMPLATE.read_text(encoding="utf-8-sig") if TEMPLATE.exists() else ""
routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
validation_text = VALIDATION.read_text(encoding="utf-8-sig") if VALIDATION.exists() else ""
integration_text = INTEGRATION.read_text(encoding="utf-8-sig") if INTEGRATION.exists() else ""
doc_text = DOC.read_text(encoding="utf-8-sig") if DOC.exists() else ""

for token in ["GET-only", "POST yoktur", "DB yazma yoktur"]:
    if token not in template_text:
        errors.append(f"passive_form.html içinde beklenen ifade yok: {token}")

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
    if forbidden in integration_text:
        errors.append(f"security_integration_contract.py içinde yazma/request izi bulundu: {forbidden}")

if digital_archive_write_is_enabled() is not False:
    errors.append("DIGITAL_ARCHIVE_WRITE_ENABLED False değil.")

if digital_archive_security_integration_is_enabled() is not False:
    errors.append("DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED False değil.")

if digital_archive_security_contract_allows_write() is not False:
    errors.append("WRITE_ALLOWED False değil.")

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
    "DA-10A1",
    "GET-only",
    "POST route açılmamıştır",
    "DB yazma yapılmamıştır",
    "Canlı ortamda işlem yapılmamıştır",
]:
    if token not in doc_text:
        errors.append(f"DA10A1 dokümanında beklenen ifade yok: {token}")

if errors:
    raise SystemExit("DA-10A1 CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-10A1 passive form GET-only note kontrolü geçti.")
print("POST_ROUTE_COUNT=", len(post_routes))
print("WRITE_ALLOWED=", digital_archive_security_contract_allows_write())
print("SONUC=DA10A1_PASSIVE_FORM_GET_NOTE_OK")
