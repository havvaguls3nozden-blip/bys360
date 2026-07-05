from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

os.environ["BYS360_DIGITAL_ARCHIVE_LOCAL_WRITE_TEST"] = "1"

from app import create_app, db  # noqa: E402
from app.digital_archive.security_integration_contract import (  # noqa: E402
    digital_archive_security_contract_allows_write,
)


ROOT = Path.cwd()
REPORT_DIR = Path(r"C:\bys360\reports\digital_archive_da14a_category_local_write_smoke_repair2_20260705_201709")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

errors = []
warnings = []

routes_path = ROOT / "app" / "digital_archive" / "routes.py"
doc_path = ROOT / "docs" / "digital_archive" / "DA14A_CATEGORY_LOCAL_SQLITE_WRITE_SMOKE.md"

for path in [routes_path, doc_path]:
    if not path.exists():
        errors.append(f"Beklenen dosya yok: {path}")

routes_text = routes_path.read_text(encoding="utf-8-sig") if routes_path.exists() else ""
doc_text = doc_path.read_text(encoding="utf-8-sig") if doc_path.exists() else ""

for token in [
    "DA-14A local SQLite kategori yazma kapısı",
    "BYS360_DIGITAL_ARCHIVE_LOCAL_WRITE_TEST",
    "DigitalArchiveCategory(",
    "db.session.add(category)",
    "db.session.commit()",
    "db.session.rollback()",
]:
    if token not in routes_text:
        errors.append(f"routes.py içinde beklenen DA-14A token yok: {token}")

for token in [
    "DA-14A",
    "Local SQLite",
    "Canlı ortamda",
    "category_create",
]:
    if token not in doc_text:
        errors.append(f"DA14A dokümanında beklenen ifade yok: {token}")

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
created_row = None
post_status_code = None
post_location = ""

test_code = "D14A" + datetime.now().strftime("%H%M%S")

payload = {
    "parent_id": "",
    "code": test_code,
    "name": "DA-14A Lokal Test Kategorisi",
    "description": "DA-14A local SQLite write smoke testi.",
    "is_active": "true",
    "sort_order": "14",
}

with app.app_context():
    if not str(db.engine.url.drivername).startswith("sqlite"):
        errors.append(f"DA-14A sadece SQLite bekliyordu. Driver: {db.engine.url.drivername}")

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

    client = app.test_client()
    response = client.post(
        "/digital-archive/categories",
        data=payload,
        follow_redirects=False,
    )

    post_status_code = response.status_code
    post_location = response.headers.get("Location", "")

    if post_status_code not in {302, 303}:
        errors.append(f"Kategori local write POST redirect dönmedi. status={post_status_code}")

    if "/digital-archive/categories" not in post_location:
        errors.append(f"Kategori local write POST redirect hedefi beklenen değil: {post_location}")

    for table in target_tables:
        after_counts[table] = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()

    created_row = db.session.execute(
        text(
            "SELECT id, code, name, is_active, sort_order "
            "FROM digital_archive_categories "
            "WHERE code = :code"
        ),
        {"code": test_code},
    ).mappings().first()

if after_counts["digital_archive_categories"] != before_counts["digital_archive_categories"] + 1:
    errors.append(
        "digital_archive_categories satır sayısı 1 artmadı: "
        f"before={before_counts['digital_archive_categories']}, "
        f"after={after_counts['digital_archive_categories']}"
    )

for table in ["digital_archive_physical_locations", "digital_archive_retention_policies"]:
    if after_counts[table] != before_counts[table]:
        errors.append(f"{table} değişmemeliydi: before={before_counts[table]}, after={after_counts[table]}")

if not created_row:
    errors.append(f"Test kategori kaydı bulunamadı: code={test_code}")

report_path = REPORT_DIR / "DA14A_CATEGORY_LOCAL_SQLITE_WRITE_SMOKE_REPORT.md"

lines = [
    "# BYS360 DA-14A Dijital Arşiv Category Local SQLite Write Smoke",
    "",
    "Bu rapor local SQLite üzerinde tek kategori yazma smoke testini kaydeder. Canlıya işlem yapılmamıştır.",
    "",
    f"- Zaman: `{datetime.now().isoformat(timespec='seconds')}`",
    f"- POST route sayısı: `{len(post_routes)}`",
    f"- POST routes: `{', '.join(sorted(post_routes))}`",
    f"- Test POST status: `{post_status_code}`",
    f"- Test POST redirect: `{post_location}`",
    f"- Test category code: `{test_code}`",
    f"- Created row: `{dict(created_row) if created_row else None}`",
    f"- Contract write allowed: `{digital_archive_security_contract_allows_write()}`",
    "",
    "## DB Satır Sayısı Kontrolü",
]

for table in target_tables:
    lines.append(f"- `{table}`: before `{before_counts.get(table)}` / after `{after_counts.get(table)}`")

lines.extend([
    "",
    "## Hatalar",
])

if errors:
    lines.extend([f"- {error}" for error in errors])
else:
    lines.append("- Yok")

lines.extend([
    "",
    "## Uyarılar",
])

if warnings:
    lines.extend([f"- {warning}" for warning in warnings])
else:
    lines.append("- Yok")

lines.extend([
    "",
    "## Sonuç",
    "OK: DA-14A category local SQLite write smoke tamamlandı. Local DB üzerinde yalnızca kategori kaydı oluşturulmuştur." if not errors else "FAIL: DA-14A hataları çözülmelidir.",
])

report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("OK: DA-14A category local SQLite write smoke tamamlandı.")
print(f"REPORT={report_path}")
print("POST_ROUTE_COUNT=", len(post_routes))
print("POST_ROUTES=", ",".join(sorted(post_routes)))
print("ERROR_COUNT=", len(errors))
print("WARNING_COUNT=", len(warnings))
print("TEST_POST_STATUS=", post_status_code)
print("TEST_POST_LOCATION=", post_location)
print("TEST_CATEGORY_CODE=", test_code)
print("CREATED_ROW_ID=", created_row["id"] if created_row else "")

for table in target_tables:
    print(f"COUNT_CHECK {table}: BEFORE={before_counts.get(table)} AFTER={after_counts.get(table)}")

if errors:
    print("SONUC=DA14A_CATEGORY_LOCAL_SQLITE_WRITE_SMOKE_FAIL")
    raise SystemExit(1)

print("SONUC=DA14A_CATEGORY_LOCAL_SQLITE_WRITE_SMOKE_OK")
