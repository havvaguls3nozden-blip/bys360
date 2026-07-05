from pathlib import Path
import py_compile

from app.digital_archive.model_contract import get_digital_archive_table_names
from app.digital_archive import models as digital_archive_models

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "app" / "digital_archive" / "models.py"

py_compile.compile(str(MODEL_PATH), doraise=True)

model_classes = [
    digital_archive_models.DigitalArchiveCategory,
    digital_archive_models.DigitalArchiveDocument,
    digital_archive_models.DigitalArchiveDocumentVersion,
    digital_archive_models.DigitalArchivePhysicalLocation,
    digital_archive_models.DigitalArchiveRetentionPolicy,
    digital_archive_models.DigitalArchiveAccessRule,
    digital_archive_models.DigitalArchiveAuditEvent,
    digital_archive_models.DigitalArchiveEntityLink,
    digital_archive_models.DigitalArchiveOcrJob,
]

model_table_names = {model.__tablename__ for model in model_classes}
contract_table_names = set(get_digital_archive_table_names())

missing_models = sorted(contract_table_names.difference(model_table_names))
extra_models = sorted(model_table_names.difference(contract_table_names))

if missing_models:
    raise SystemExit("DA-2B FAIL: Modeli eksik tablolar:\n" + "\n".join(missing_models))

if extra_models:
    raise SystemExit("DA-2B FAIL: Sözleşmede olmayan model tabloları:\n" + "\n".join(extra_models))

for model in model_classes:
    table_name = model.__tablename__
    if not table_name.startswith("digital_archive_"):
        raise SystemExit(f"DA-2B FAIL: Prefix dışı tablo: {table_name}")

    for column in model.__table__.columns:
        for foreign_key in column.foreign_keys:
            target = foreign_key.target_fullname
            if not (
                target.startswith("digital_archive_")
                or target.startswith("users.")
                or target.startswith("organization_units.")
            ):
                raise SystemExit(
                    "DA-2B FAIL: İzin verilmeyen FK hedefi: "
                    f"{table_name}.{column.name} -> {target}"
                )

model_text = MODEL_PATH.read_text(encoding="utf-8")
for forbidden in ("except Exception", "except:", "bare except"):
    if forbidden in model_text:
        raise SystemExit(f"DA-2B FAIL: Geniş except bulundu: {forbidden}")

required_relationships = [
    "DigitalArchiveDocument",
    "DigitalArchiveDocumentVersion",
    "DigitalArchiveAccessRule",
    "DigitalArchiveAuditEvent",
    "DigitalArchiveEntityLink",
    "DigitalArchiveOcrJob",
]
for name in required_relationships:
    if name not in model_text:
        raise SystemExit(f"DA-2B FAIL: Beklenen model adı yok: {name}")

print("OK: DA-2B Dijital Arşiv SQLAlchemy model sözleşmesi geçti.")
print("MODELS:")
for model in model_classes:
    print(f"- {model.__name__} -> {model.__tablename__}")
