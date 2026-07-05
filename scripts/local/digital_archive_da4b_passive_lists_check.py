
from pathlib import Path

from app import create_app
from app.digital_archive import models as _digital_archive_models  # noqa: F401


ROOT = Path.cwd()
ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
INDEX_TEMPLATE = ROOT / "app" / "templates" / "digital_archive" / "index.html"
PASSIVE_LIST_TEMPLATE = ROOT / "app" / "templates" / "digital_archive" / "passive_list.html"

TARGETS = [
    ("/digital-archive/categories", "Arşiv Kategorileri", "digital_archive_categories"),
    ("/digital-archive/physical-locations", "Fiziksel Konumlar", "digital_archive_physical_locations"),
    ("/digital-archive/retention-policies", "Saklama Politikaları", "digital_archive_retention_policies"),
]

errors = []

for path in [ROUTES, INDEX_TEMPLATE, PASSIVE_LIST_TEMPLATE]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
index_text = INDEX_TEMPLATE.read_text(encoding="utf-8-sig") if INDEX_TEMPLATE.exists() else ""
passive_text = PASSIVE_LIST_TEMPLATE.read_text(encoding="utf-8-sig") if PASSIVE_LIST_TEMPLATE.exists() else ""

required_route_tokens = [
    "_DIGITAL_ARCHIVE_PASSIVE_LIST_SPECS",
    "_safe_table_rows",
    "_digital_archive_passive_list_context",
    "@digital_archive_bp.get(\"/categories\")",
    "@digital_archive_bp.get(\"/physical-locations\")",
    "@digital_archive_bp.get(\"/retention-policies\")",
]

for token in required_route_tokens:
    if token not in routes_text:
        errors.append(f"routes.py içinde beklenen ifade yok: {token}")

for route, title, table_name in TARGETS:
    if route not in index_text:
        errors.append(f"index.html içinde link yok: {route}")
    if title not in routes_text and title not in index_text:
        errors.append(f"Beklenen ekran başlığı yok: {title}")
    if table_name not in routes_text:
        errors.append(f"routes.py içinde hedef tablo yok: {table_name}")

for token in ["{{ page_title }}", "Liste", "Salt-okunur", "row_count", "columns", "rows"]:
    if token not in passive_text:
        errors.append(f"passive_list.html içinde beklenen ifade yok: {token}")

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
        for token in [title, table_name, "Salt-okunur"]:
            if token not in body:
                errors.append(f"{route} response içinde beklenen ifade yok: {token}")

if errors:
    raise SystemExit("DA-4B CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-4B pasif liste ekranları kontrolü geçti.")
print("ROUTES=", ", ".join(route for route, _, _ in TARGETS))
print("SONUC=DA4B_PASSIVE_LISTS_CHECK_OK")
