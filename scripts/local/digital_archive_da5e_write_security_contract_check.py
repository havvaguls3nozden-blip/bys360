from pathlib import Path

from app import create_app


ROOT = Path.cwd()

ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
PASSIVE_FORM = ROOT / "app" / "templates" / "digital_archive" / "passive_form.html"
CONTRACT = ROOT / "docs" / "digital_archive" / "DA5E_WRITE_SECURITY_CONTRACT.md"

TARGET_GET_ROUTES = [
    "/digital-archive/categories/new",
    "/digital-archive/physical-locations/new",
    "/digital-archive/retention-policies/new",
]

errors = []

for path in [ROUTES, PASSIVE_FORM, CONTRACT]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
form_text = PASSIVE_FORM.read_text(encoding="utf-8-sig") if PASSIVE_FORM.exists() else ""
contract_text = CONTRACT.read_text(encoding="utf-8-sig") if CONTRACT.exists() else ""

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

for token in [
    "GET-only taslak form",
    "DB yazma işlemi yapmaz",
    "@digital_archive_bp.get(\"/categories/new\")",
    "@digital_archive_bp.get(\"/physical-locations/new\")",
    "@digital_archive_bp.get(\"/retention-policies/new\")",
]:
    if token not in routes_text:
        errors.append(f"routes.py içinde beklenen GET-only iz yok: {token}")

for token in [
    "POST yok / DB yazma kapalı",
    "Veri yazma kapalı",
    "disabled",
]:
    if token not in form_text:
        errors.append(f"passive_form.html içinde beklenen pasif form izi yok: {token}")

for forbidden in [
    "<form",
    "method=\"post\"",
    "method='post'",
    "type=\"submit\"",
]:
    if forbidden.lower() in form_text.lower():
        errors.append(f"passive_form.html içinde aktif form/kayıt izi bulundu: {forbidden}")

for token in [
    "Yetki Kontrolü",
    "CSRF Koruması",
    "Sunucu Tarafı Validasyon",
    "Whitelist Alan Yazımı",
    "Audit Event",
    "Transaction Güvenliği",
    "Soft Delete",
    "Canlıya Geçiş Öncesi Kontroller",
    "GET-only ve DB yazmasızdır",
]:
    if token not in contract_text:
        errors.append(f"Sözleşme dokümanında beklenen başlık yok: {token}")

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
    raise SystemExit("DA-5E CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-5E yazma güvenliği sözleşmesi ve guard kontrolü geçti.")
print("TARGET_GET_ROUTE_COUNT=", len(TARGET_GET_ROUTES))
print("SONUC=DA5E_WRITE_SECURITY_CONTRACT_OK")
