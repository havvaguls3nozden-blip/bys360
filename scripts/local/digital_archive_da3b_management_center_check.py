from pathlib import Path

from app import create_app
from app.digital_archive.model_contract import get_digital_archive_table_names
from app.digital_archive import models as _digital_archive_models  # noqa: F401


ROOT = Path.cwd()
ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
INDEX_TEMPLATE = ROOT / "app" / "templates" / "digital_archive" / "index.html"

errors = []

if not ROUTES.exists():
    errors.append("routes.py yok.")

if not INDEX_TEMPLATE.exists():
    errors.append("digital_archive/index.html yok.")

routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
template_text = INDEX_TEMPLATE.read_text(encoding="utf-8-sig") if INDEX_TEMPLATE.exists() else ""

required_route_tokens = [
    'render_template("digital_archive/index.html"',
    "_digital_archive_dashboard_context",
    "_safe_table_count",
    "SQLAlchemyError",
    '"page_title": "Dijital Arşiv Yönetim Merkezi"',
    '"module_status": "Pasif güvenli ekran"',
]

for token in required_route_tokens:
    if token not in routes_text:
        errors.append(f"routes.py içinde beklenen ifade yok: {token}")

required_template_tokens = [
    "{{ page_title }}",
    "{{ module_status }}",
    "Altyapı Durumu",
    "Canlı işlem yok",
    "table_cards",
    "summary.ready_table_count",
    "summary.table_count",
]

for token in required_template_tokens:
    if token not in template_text:
        errors.append(f"index.html içinde beklenen ifade yok: {token}")

app = create_app()

with app.app_context():
    route_found = False
    endpoint_found = False

    for rule in app.url_map.iter_rules():
        if str(rule.rule) == "/digital-archive/":
            route_found = True
        if rule.endpoint == "digital_archive.index":
            endpoint_found = True

    if not route_found:
        errors.append("/digital-archive/ route bulunamadı.")

    if not endpoint_found:
        errors.append("digital_archive.index endpoint bulunamadı.")

    metadata_tables = set(app.extensions["sqlalchemy"].metadata.tables.keys())
    expected_tables = set(get_digital_archive_table_names())
    missing_metadata = sorted(expected_tables.difference(metadata_tables))

    if missing_metadata:
        errors.append("Metadata eksik: " + ", ".join(missing_metadata))

if errors:
    raise SystemExit("DA-3B CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-3B Dijital Arşiv Yönetim Merkezi kontrolü geçti.")
print("TEMPLATE=app/templates/digital_archive/index.html")
print("ROUTE=/digital-archive/")
print("EXPECTED_TABLE_COUNT=", len(get_digital_archive_table_names()))
print("SONUC=DA3B_MANAGEMENT_CENTER_CHECK_OK")
