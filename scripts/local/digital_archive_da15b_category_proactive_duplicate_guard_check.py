from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import text

os.environ.pop("BYS360_DIGITAL_ARCHIVE_LOCAL_WRITE_TEST", None)

from app import create_app, db  # noqa: E402
from app.digital_archive.security_integration_contract import (  # noqa: E402
    digital_archive_security_contract_allows_write,
)


ROOT = Path.cwd()

ROUTES = ROOT / "app" / "digital_archive" / "routes.py"
DOC = ROOT / "docs" / "digital_archive" / "DA15B_CATEGORY_PROACTIVE_DUPLICATE_GUARD.md"

errors = []

for path in [ROUTES, DOC]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

routes_text = ROUTES.read_text(encoding="utf-8-sig") if ROUTES.exists() else ""
doc_text = DOC.read_text(encoding="utf-8-sig") if DOC.exists() else ""

for token in [
    "DA-15B proaktif duplicate code kontrolü",
    "existing_category = DigitalArchiveCategory.query.filter_by(code=code_value).first()",
    "Bu kategori kodu zaten kayıtlıdır",
    "return redirect(\"/digital-archive/categories\")",
    "code=code_value",
]:
    if token not in routes_text:
        errors.append(f"routes.py içinde beklenen DA-15B token yok: {token}")

for token in [
    "DA-15B",
    "duplicate",
    "DB yazma yapmaz",
    "WRITE_ALLOWED = False",
]:
    if token not in doc_text:
        errors.append(f"DA15B dokümanında beklenen ifade yok: {token}")

if os.getenv("BYS360_DIGITAL_ARCHIVE_LOCAL_WRITE_TEST") is not None:
    errors.append("BYS360_DIGITAL_ARCHIVE_LOCAL_WRITE_TEST env kapalı olmalıydı.")

if digital_archive_security_contract_allows_write() is not False:
    errors.append("WRITE_ALLOWED False değil.")

app = create_app()
app.config["TESTING"] = True
app.config["LOGIN_DISABLED"] = True
app.config["DIGITAL_ARCHIVE_ENABLED"] = True
app.config["WTF_CSRF_ENABLED"] = False

target_tables = [
    "digital_archive_categories",
    "digital_archive_physical_locations",
    "digital_archive_retention_policies",
]

route_methods = {}
post_routes = []
before_counts = {}
after_counts = {}

with app.app_context():
    for table in target_tables:
        before_counts[table] = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()

    for rule in app.url_map.iter_rules():
        rule_text = str(rule.rule)

        if not rule_text.startswith("/digital-archive"):
            continue

        methods = sorted(method for method in rule.methods if method not in {"HEAD", "OPTIONS"})
        route_methods[rule_text] = methods

        if "POST" in methods:
            post_routes.append(rule_text)

    if sorted(post_routes) != ["/digital-archive/categories"]:
        errors.append(f"POST route listesi beklenen değil: {post_routes}")

    for table in target_tables:
        after_counts[table] = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()

for table in target_tables:
    if before_counts[table] != after_counts[table]:
        errors.append(f"{table} değişmemeliydi: before={before_counts[table]}, after={after_counts[table]}")

if errors:
    raise SystemExit("DA-15B CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-15B category proactive duplicate guard kontrolü geçti.")
print("POST_ROUTE_COUNT=", len(post_routes))
print("POST_ROUTES=", ",".join(sorted(post_routes)))
print("WRITE_ALLOWED=", digital_archive_security_contract_allows_write())

for table in target_tables:
    print(f"COUNT_CHECK {table}: BEFORE={before_counts[table]} AFTER={after_counts[table]}")

print("SONUC=DA15B_CATEGORY_PROACTIVE_DUPLICATE_GUARD_OK")
