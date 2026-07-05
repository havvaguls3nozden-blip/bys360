from pathlib import Path

from sqlalchemy import text

from app import create_app, db
from app.digital_archive.security_contract import digital_archive_write_is_enabled
from app.digital_archive.security_integration_contract import (
    digital_archive_security_contract_allows_write,
    digital_archive_security_integration_is_enabled,
)


ROOT = Path.cwd()

ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
DOC = ROOT / "docs" / "digital_archive" / "DA12C_CATEGORY_GUARD_ONLY_POST_ROUTE.md"

errors = []

for path in [ROUTES, DOC]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
doc_text = DOC.read_text(encoding="utf-8-sig") if DOC.exists() else ""

required_route_tokens = [
    '@digital_archive_bp.route("/categories", methods=["POST"])',
    "def category_create_guard_only_post",
    'build_digital_archive_write_intent("category_create"',
    'redirect("/digital-archive/categories")',
]

for token in required_route_tokens:
    if token not in routes_text:
        errors.append(f"routes.py içinde beklenen DA-12C token yok: {token}")

for forbidden in [
    "db.session.add",
    "db.session.merge",
    "db.session.delete",
    "db.session.commit",
    "db.session.flush",
    ".add(",
    ".commit(",
    ".flush(",
]:
    if forbidden in routes_text:
        errors.append(f"routes.py içinde DA-12C için yasaklı DB yazma izi bulundu: {forbidden}")

if digital_archive_write_is_enabled() is not False:
    errors.append("DIGITAL_ARCHIVE_WRITE_ENABLED False değil.")

if digital_archive_security_integration_is_enabled() is not False:
    errors.append("DIGITAL_ARCHIVE_SECURITY_INTEGRATION_ENABLED False değil.")

if digital_archive_security_contract_allows_write() is not False:
    errors.append("WRITE_ALLOWED False değil.")

for token in [
    "DA-12C",
    "guard-only",
    "/digital-archive/categories",
    "DB yazma yapılmamıştır",
    "Canlı ortamda işlem yapılmamıştır",
    "WRITE_ALLOWED = False",
]:
    if token not in doc_text:
        errors.append(f"DA12C dokümanında beklenen ifade yok: {token}")

app = create_app()
app.config["TESTING"] = True
app.config["LOGIN_DISABLED"] = True
app.config["DIGITAL_ARCHIVE_ENABLED"] = True

route_methods = {}
post_routes = []
counts_before = {}
counts_after = {}

target_tables = [
    "digital_archive_categories",
    "digital_archive_physical_locations",
    "digital_archive_retention_policies",
]

with app.app_context():
    for table in target_tables:
        counts_before[table] = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()

    for rule in app.url_map.iter_rules():
        rule_text = str(rule.rule)

        if not rule_text.startswith("/digital-archive"):
            continue

        methods = sorted(method for method in rule.methods if method not in {"HEAD", "OPTIONS"})
        route_methods[rule_text] = methods

        if "POST" in methods:
            post_routes.append(rule_text)

    for table in target_tables:
        counts_after[table] = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()

if post_routes != ["/digital-archive/categories"]:
    errors.append(f"POST route listesi beklenen değil: {post_routes}")

if route_methods.get("/digital-archive/categories/new") != ["GET"]:
    errors.append(f"Kategori GET taslak route GET-only değil: {route_methods.get('/digital-archive/categories/new')}")

if "POST" not in route_methods.get("/digital-archive/categories", []):
    errors.append("Kategori POST route app route map içinde yok.")

for table in target_tables:
    if counts_before[table] != counts_after[table]:
        errors.append(f"{table} satır sayısı değişti: before={counts_before[table]}, after={counts_after[table]}")

if errors:
    raise SystemExit("DA-12C CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-12C category guard-only POST route kontrolü geçti.")
print("POST_ROUTE_COUNT=", len(post_routes))
print("POST_ROUTES=", ",".join(post_routes))
print("WRITE_ALLOWED=", digital_archive_security_contract_allows_write())

for table in target_tables:
    print(f"COUNT_CHECK {table}: BEFORE={counts_before[table]} AFTER={counts_after[table]}")

print("SONUC=DA12C_CATEGORY_GUARD_ONLY_POST_ROUTE_OK")
