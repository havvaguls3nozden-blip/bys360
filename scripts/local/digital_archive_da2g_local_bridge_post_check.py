from pathlib import Path
import sqlite3
from datetime import datetime

from app import create_app, db
from app.digital_archive.model_contract import get_digital_archive_table_names
from app.digital_archive import models as _digital_archive_models  # noqa: F401


TARGET_REVISION = "da2d_digital_archive_20260705"

REQUIRED_CORE_TABLES = {
    "users",
    "organization_units",
    "user_menu_permissions",
    "performance_periods",
    "performance_criteria",
    "communication_bulletins",
    "messages",
    "notifications",
    "surveys",
    "personnel_documents",
}

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_dir = Path(r"C:\bys360\reports") / f"digital_archive_da2g_local_bridge_post_check_{stamp}"
report_dir.mkdir(parents=True, exist_ok=True)
report_path = report_dir / "DA2G_LOCAL_BRIDGE_POST_CHECK_REPORT.md"

app = create_app()

with app.app_context():
    dialect = db.engine.url.get_backend_name()
    db_path = Path(db.engine.url.database or "")
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path

    metadata_tables = set(db.metadata.tables.keys())
    expected_da = set(get_digital_archive_table_names())
    db.engine.dispose()

if dialect != "sqlite":
    raise SystemExit(f"DA-2G POST CHECK FAIL: Bu kontrol lokal SQLite içindir. DIALECT={dialect}")

conn = sqlite3.connect(db_path)

try:
    tables = {
        row[0]
        for row in conn.execute(
            "select name from sqlite_master where type='table'"
        ).fetchall()
    }

    versions = []
    if "alembic_version" in tables:
        versions = [
            row[0]
            for row in conn.execute(
                "select version_num from alembic_version order by version_num"
            ).fetchall()
        ]

    columns = {}
    for table in expected_da.intersection(tables):
        columns[table] = [
            row[1]
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        ]

    errors = []

    if set(versions) != {TARGET_REVISION}:
        errors.append(f"Alembic revision beklenen hedefte değil. Bulunan={versions}")

    missing_da_db = sorted(expected_da.difference(tables))
    if missing_da_db:
        errors.append("DB'de eksik Dijital Arşiv tabloları: " + ", ".join(missing_da_db))

    missing_da_metadata = sorted(expected_da.difference(metadata_tables))
    if missing_da_metadata:
        errors.append("Metadata içinde eksik Dijital Arşiv tabloları: " + ", ".join(missing_da_metadata))

    missing_core = sorted(REQUIRED_CORE_TABLES.difference(tables))
    if missing_core:
        errors.append("Eksik çekirdek tablolar: " + ", ".join(missing_core))

    empty_column_tables = sorted(
        table for table in expected_da
        if table in tables and not columns.get(table)
    )
    if empty_column_tables:
        errors.append("Kolon bilgisi okunamayan Dijital Arşiv tabloları: " + ", ".join(empty_column_tables))

    if errors:
        raise SystemExit("DA-2G POST CHECK FAIL:\n" + "\n".join(errors))

    lines = [
        "# BYS360 DA-2G Local Bridge Post Check",
        "",
        f"- Zaman: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- DB path: `{db_path}`",
        f"- Dialect: `{dialect}`",
        f"- Target revision: `{TARGET_REVISION}`",
        "",
        "## Alembic revisions",
        *[f"- `{version}`" for version in versions],
        "",
        "## Dijital Arşiv tabloları",
        *[f"- `{table}` — kolon sayısı: `{len(columns.get(table, []))}`" for table in sorted(expected_da)],
        "",
        "## Çekirdek tablo kontrolü",
        f"- Kontrol edilen çekirdek tablo sayısı: `{len(REQUIRED_CORE_TABLES)}`",
        "- Eksik çekirdek tablo: `0`",
        "",
        "## Sonuç",
        "OK: DA-2G local bridge sonrası lokal SQLite DB güvenli ve Dijital Arşiv tabloları hazır.",
    ]

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("OK: DA-2G local bridge post-check geçti.")
    print(f"REPORT={report_path}")
    print("DIGITAL_ARCHIVE_TABLE_COUNT=", len(expected_da))
    print("ALEMBIC_REVISIONS=", ", ".join(versions))
    print("SONUC=DA2G_LOCAL_BRIDGE_POST_CHECK_OK")

finally:
    conn.close()
