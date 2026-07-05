
from pathlib import Path

from app import create_app
from app.digital_archive import models as _digital_archive_models  # noqa: F401


ROOT = Path.cwd()
ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
PASSIVE_LIST_TEMPLATE = ROOT / "app" / "templates" / "digital_archive" / "passive_list.html"
PASSIVE_FORM_TEMPLATE = ROOT / "app" / "templates" / "digital_archive" / "passive_form.html"

TARGETS = [
    ("/digital-archive/categories/new", "Arşiv Kategorileri Taslak Formu", "digital_archive_categories"),
    ("/digital-archive/physical-locations/new", "Fiziksel Konumlar Taslak Formu", "digital_archive_physical_locations"),
    ("/digital-archive/retention-policies/new", "Saklama Politikaları Taslak Formu", "digital_archive_retention_policies"),
]

errors = []

for path in [ROUTES, PASSIVE_LIST_TEMPLATE, PASSIVE_FORM_TEMPLATE]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
list_text = PASSIVE_LIST_TEMPLATE.read_text(encoding="utf-8-sig") if PASSIVE_LIST_TEMPLATE.exists() else ""
form_text = PASSIVE_FORM_TEMPLATE.read_text(encoding="utf-8-sig") if PASSIVE_FORM_TEMPLATE.exists() else ""

required_route_tokens = [
    "DA-5B: Dijital Arşiv GET-only taslak form ekranları",
    "_digital_archive_passive_form_context",
    "@digital_archive_bp.get(\"/categories/new\")",
    "@digital_archive_bp.get(\"/physical-locations/new\")",
    "@digital_archive_bp.get(\"/retention-policies/new\")",
]

for token in required_route_tokens:
    if token not in routes_text:
        errors.append(f"routes.py içinde beklenen ifade yok: {token}")

for forbidden in [
    "@digital_archive_bp.post",
    "methods=[\"POST\"]",
    "methods=['POST']",
    "db.session.add",
    "db.session.commit",
    "request.form",
]:
    if forbidden in routes_text:
        errors.append(f"routes.py içinde DA-5B için yasaklı yazma izi var: {forbidden}")

for token in [
    "Taslak Formu Gör",
    "draft_form_url",
]:
    if token not in list_text:
        errors.append(f"passive_list.html içinde beklenen bağlantı izi yok: {token}")

for token in [
    "Taslak Form",
    "POST yok / DB yazma kapalı",
    "Veri yazma kapalı",
    "role=\"form\"",
    "disabled",
]:
    if token not in form_text:
        errors.append(f"passive_form.html içinde beklenen ifade yok: {token}")

app = create_app()
app.config["TESTING"] = True
app.config["LOGIN_DISABLED"] = True
app.config["DIGITAL_ARCHIVE_ENABLED"] = True

with app.app_context():
    client = app.test_client()
    route_rules = {str(rule.rule) for rule in app.url_map.iter_rules()}

    for route, title, table_name in TARGETS:
        if route not in route_rules:
            errors.append(f"Route bulunamadı: {route}")

        response = client.get(route, follow_redirects=True)

        if response.status_code != 200:
            errors.append(f"{route} beklenen 200 değil: {response.status_code}")
            continue

        body = response.get_data(as_text=True)
        for token in [title, table_name, "Veri yazma kapalı", "POST yok"]:
            if token not in body:
                errors.append(f"{route} response içinde beklenen ifade yok: {token}")

if errors:
    raise SystemExit("DA-5B CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-5B GET-only taslak form ekranları kontrolü geçti.")
print("ROUTES=", ", ".join(route for route, _, _ in TARGETS))
print("SONUC=DA5B_GET_ONLY_FORMS_CHECK_OK")
