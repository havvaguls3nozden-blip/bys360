from pathlib import Path
import py_compile

from app import db

# Dijital Arşiv modelleri migration metadata'ya bilerek dahil ediliyor.
from app.digital_archive import models as digital_archive_models  # noqa: F401
from app.digital_archive.model_contract import get_digital_archive_table_names

expected_tables = set(get_digital_archive_table_names())
metadata_tables = set(db.metadata.tables.keys())

missing = sorted(expected_tables.difference(metadata_tables))
if missing:
    raise SystemExit(
        "DA-2C PRE FAIL: Dijital Arşiv tabloları db.metadata içine girmedi:\n"
        + "\n".join(missing)
    )

unexpected_existing_scope = sorted(
    table_name
    for table_name in metadata_tables
    if table_name.startswith("digital_archive_") and table_name not in expected_tables
)
if unexpected_existing_scope:
    raise SystemExit(
        "DA-2C PRE FAIL: Sözleşme dışı digital_archive tablosu metadata içinde var:\n"
        + "\n".join(unexpected_existing_scope)
    )

model_path = Path("app/digital_archive/models.py")
py_compile.compile(str(model_path), doraise=True)

print("OK: DA-2C PRE Dijital Arşiv modelleri db.metadata içinde görünüyor.")
print("DIGITAL_ARCHIVE_METADATA_TABLES:")
for table_name in sorted(expected_tables):
    print(f"- {table_name}")

print("TOTAL_METADATA_TABLES=", len(metadata_tables))
