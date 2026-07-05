
from pathlib import Path

from app import create_app
from app.digital_archive.security_contract import digital_archive_write_is_enabled


ROOT = Path.cwd()

ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
INDEX_TEMPLATE = ROOT / "app" / "templates" / "digital_archive" / "index.html"
SECURITY_TEMPLATE = ROOT / "app" / "templates" / "digital_archive" / "security_status.html"

errors = []

for path in [ROUTES, INDEX_TEMPLATE, SECURITY_TEMPLATE]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
index_text = INDEX_TEMPLATE.read_text(encoding="utf-8-sig") if INDEX_TEMPLATE.exists() else ""
security_text = SECURITY_TEMPLATE.read_text(encoding="utf-8-sig") if SECURITY_TEMPLATE.exists() else ""

for token in [
    "DA-6C: Dijital Arşiv güvenlik durumu ekranı",
    "@digital_archive_bp.get(\"/security\")",
    "digital_archive_write_is_enabled",
    "get_digital_archive_write_operations",
    "get_digital_archive_write_security_requirements",
]:
    if token not in routes_text:
        errors.append(f"routes.py içinde beklenen ifade yok: {token}")

for forbidden in [
    "@digital_archive_bp.post",
    "methods=[\"POST\"]",
    "methods=['POST']",
    "request.form",
    "request.get_json",
    "db.session.add",
    "db.session.commit",
]:
    if forbidden in routes_text:
        errors.append(f"routes.py içinde yazma izi bulundu: {forbidden}")

for token in [
    "/digital-archive/security",
    "Güvenlik Durumu",
]:
    if token not in index_text:
        errors.append(f"index.html içinde güvenlik ekranı bağlantısı yok: {token}")

for token in [
    "Dijital Arşiv Güvenlik Durumu",
    "Yazma Kapalı",
    "POST yok / DB yazma kapalı",
    "Planlanan Yazma Operasyonları",
    "Zorunlu Güvenlik Gereksinimleri",
]:
    if token not in security_text:
        errors.append(f"security_status.html içinde beklenen ifade yok: {token}")

if digital_archive_write_is_enabled() is not False:
    errors.append("digital_archive_write_is_enabled() False dönmüyor.")

app = create_app()
app.config["TESTING"] = True
app.config["LOGIN_DISABLED"] = True
app.config["DIGITAL_ARCHIVE_ENABLED"] = True

with app.app_context():
    client = app.test_client()

    route_methods = {}
    for rule in app.url_map.iter_rules():
        rule_text = str(rule.rule)
        if rule_text.startswith("/digital-archive"):
            route_methods[rule_text] = sorted(
                method for method in rule.methods if method not in {"HEAD", "OPTIONS"}
            )

    if route_methods.get("/digital-archive/security") != ["GET"]:
        errors.append(f"/digital-archive/security yalnızca GET değil: {route_methods.get('/digital-archive/security')}")

    post_routes = [
        route for route, methods in route_methods.items()
        if "POST" in methods
    ]

    if post_routes:
        errors.append(f"Dijital Arşiv içinde POST route bulundu: {post_routes}")

    response = client.get("/digital-archive/security", follow_redirects=True)
    if response.status_code != 200:
        errors.append(f"/digital-archive/security beklenen 200 değil: {response.status_code}")
    else:
        body = response.get_data(as_text=True)
        for token in [
            "Dijital Arşiv Güvenlik Durumu",
            "Yazma Kapalı",
            "category_create",
            "physical_location_create",
            "retention_policy_create",
            "route_level_permission_check",
            "csrf_validation",
        ]:
            if token not in body:
                errors.append(f"/digital-archive/security response içinde beklenen ifade yok: {token}")

if errors:
    raise SystemExit("DA-6C CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-6C güvenlik durumu ekranı kontrolü geçti.")
print("ROUTE=/digital-archive/security")
print("WRITE_ENABLED=", digital_archive_write_is_enabled())
print("SONUC=DA6C_SECURITY_STATUS_SCREEN_OK")
