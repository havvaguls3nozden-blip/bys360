from pathlib import Path

from sqlalchemy import inspect as sa_inspect

from app import create_app, db
from app.digital_archive.security_contract import (
    digital_archive_write_is_enabled,
    get_digital_archive_field_whitelist,
    get_digital_archive_field_write_exclusions,
    get_digital_archive_write_operations,
)


ROOT = Path.cwd()

MODULE = ROOT / "app" / "digital_archive" / "security_contract.py"
ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
DOC = ROOT / "docs" / "digital_archive" / "DA7B_WHITELIST_DB_ALIGNMENT.md"

EXPECTED_WHITELISTS = {
    "category_create": (
        "parent_id",
        "code",
        "name",
        "description",
        "is_active",
        "sort_order",
    ),
    "physical_location_create": (
        "archive_room",
        "cabinet_no",
        "shelf_no",
        "box_no",
        "folder_no",
        "file_no",
        "physical_status",
    ),
    "retention_policy_create": (
        "name",
        "retention_years",
        "action",
        "requires_approval",
        "description",
        "is_active",
    ),
}

EXPECTED_EXCLUSIONS = {
    "category_create": (),
    "physical_location_create": (
        "delivered_to_user_id",
        "delivered_at",
        "returned_at",
    ),
    "retention_policy_create": (),
}

SYSTEM_COLUMNS = {
    "id",
    "created_at",
    "updated_at",
    "deleted_at",
    "created_by",
    "updated_by",
    "deleted_by",
    "created_by_id",
    "updated_by_id",
    "deleted_by_id",
}

errors = []

for path in [MODULE, ROUTES, DOC]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

module_text = MODULE.read_text(encoding="utf-8-sig") if MODULE.exists() else ""
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
    if forbidden in module_text:
        errors.append(f"security_contract.py içinde yazma izi bulundu: {forbidden}")

if "DIGITAL_ARCHIVE_WRITE_ENABLED = False" not in module_text:
    errors.append("security_contract.py içinde WRITE_ENABLED False izi yok.")

if "DIGITAL_ARCHIVE_FIELD_WRITE_EXCLUSIONS" not in module_text:
    errors.append("security_contract.py içinde write exclusion sözleşmesi yok.")

if digital_archive_write_is_enabled() is not False:
    errors.append("digital_archive_write_is_enabled() False dönmüyor.")

app = create_app()
app.config["TESTING"] = True
app.config["LOGIN_DISABLED"] = True
app.config["DIGITAL_ARCHIVE_ENABLED"] = True

with app.app_context():
    inspector = sa_inspect(db.engine)
    table_names = set(inspector.get_table_names())
    operations = get_digital_archive_write_operations()

    for key, expected_whitelist in EXPECTED_WHITELISTS.items():
        operation = operations.get(key)
        if operation is None:
            errors.append(f"Beklenen operasyon yok: {key}")
            continue

        if operation.table_name not in table_names:
            errors.append(f"Operasyon tablosu DB'de yok: {operation.table_name}")
            continue

        columns = [column["name"] for column in inspector.get_columns(operation.table_name)]
        db_column_set = set(columns)

        whitelist = tuple(get_digital_archive_field_whitelist(key))
        exclusions = tuple(get_digital_archive_field_write_exclusions(key))

        if whitelist != expected_whitelist:
            errors.append(f"{key} whitelist beklenenle aynı değil. Beklenen={expected_whitelist}, Gelen={whitelist}")

        if exclusions != EXPECTED_EXCLUSIONS[key]:
            errors.append(f"{key} exclusion beklenenle aynı değil. Beklenen={EXPECTED_EXCLUSIONS[key]}, Gelen={exclusions}")

        for field in whitelist:
            if field not in db_column_set:
                errors.append(f"{key} whitelist alanı DB kolonunda yok: {field}")

        for field in exclusions:
            if field not in db_column_set:
                errors.append(f"{key} exclusion alanı DB kolonunda yok: {field}")

        overlap = set(whitelist).intersection(exclusions)
        if overlap:
            errors.append(f"{key} whitelist ve exclusion çakışıyor: {sorted(overlap)}")

        unmanaged_candidates = [
            column for column in columns
            if column not in SYSTEM_COLUMNS
            and column not in whitelist
            and column not in exclusions
        ]

        if unmanaged_candidates:
            errors.append(f"{key} whitelist/exclusion dışında kalan aday kolon var: {unmanaged_candidates}")

    route_methods = {}
    for rule in app.url_map.iter_rules():
        rule_text = str(rule.rule)
        if rule_text.startswith("/digital-archive"):
            route_methods[rule_text] = sorted(
                method for method in rule.methods if method not in {"HEAD", "OPTIONS"}
            )

    post_routes = [
        route for route, methods in route_methods.items()
        if "POST" in methods
    ]

    if post_routes:
        errors.append(f"Dijital Arşiv içinde POST route bulundu: {post_routes}")

for token in [
    "DA-7B",
    "DIGITAL_ARCHIVE_WRITE_ENABLED = False",
    "POST route yoktur",
    "DB yazma yoktur",
    "delivered_to_user_id",
    "requires_approval",
]:
    if token not in doc_text:
        errors.append(f"DA7B dokümanında beklenen ifade yok: {token}")

if errors:
    raise SystemExit("DA-7B CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-7B whitelist / DB kolon hizalama kontrolü geçti.")
print("WRITE_ENABLED=", digital_archive_write_is_enabled())
print("OPERATION_COUNT=", len(EXPECTED_WHITELISTS))
print("SONUC=DA7B_WHITELIST_DB_ALIGNMENT_OK")
