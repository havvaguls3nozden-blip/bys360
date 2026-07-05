from pathlib import Path
import shutil

from sqlalchemy import inspect

from app import create_app, db
from app.digital_archive import models as digital_archive_models  # noqa: F401
from app.digital_archive.model_contract import get_digital_archive_table_names


REPORT_DIR = Path(r"C:\\bys360\\reports\\digital_archive_da2e_pre_upgrade_20260705_131557")
BACKUP_DIR = Path(r"C:\\bys360\\backups\\digital_archive_da2e_pre_upgrade_20260705_131557")

REPORT_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

report_path = REPORT_DIR / "DA2E_PRE_UPGRADE_REPORT.md"

app = create_app()

with app.app_context():
    engine = db.engine
    url = engine.url
    dialect = url.get_backend_name()

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = set(get_digital_archive_table_names())

    existing_digital_archive_tables = sorted(
        table_name
        for table_name in existing_tables
        if table_name.startswith("digital_archive_")
    )

    lines = [
        "# BYS360 DA-2E PRE Upgrade Öncesi Güvenlik Raporu",
        "",
        "Bu rapor migration uygulamaz.",
        "",
        f"- DB dialect: {dialect}",
        f"- DB url: {url.render_as_string(hide_password=True)}",
        f"- Beklenen digital_archive_* tablo sayısı: {len(expected_tables)}",
        f"- Mevcut DB içindeki digital_archive_* tablo sayısı: {len(existing_digital_archive_tables)}",
        "",
        "## Beklenen Dijital Arşiv tabloları",
    ]

    for table_name in sorted(expected_tables):
        exists_text = "DB'de mevcut" if table_name in existing_tables else "DB'de yok"
        lines.append(f"- {table_name}: {exists_text}")

    if existing_digital_archive_tables:
        lines.extend(["", "## Uyarı: DB'de mevcut digital_archive_* tabloları"])
        for table_name in existing_digital_archive_tables:
            lines.append(f"- {table_name}")

    if dialect == "sqlite":
        db_path = Path(url.database or "")
        if not db_path.is_absolute():
            db_path = Path.cwd() / db_path

        if not db_path.exists():
            raise SystemExit(f"DA-2E PRE FAIL: SQLite DB dosyası bulunamadı: {db_path}")

        backup_path = BACKUP_DIR / db_path.name
        shutil.copy2(db_path, backup_path)

        lines.extend(
            [
                "",
                "## SQLite yedek",
                f"- Kaynak: {db_path}",
                f"- Yedek: {backup_path}",
            ]
        )

    else:
        raise SystemExit(
            "DA-2E PRE FAIL: Lokal DB SQLite değil. "
            "PostgreSQL ise önce pg_dump ile ayrıca yedek alınmalı."
        )

    if existing_digital_archive_tables:
        raise SystemExit(
            "DA-2E PRE FAIL: DB içinde digital_archive_* tablo zaten var. "
            "Upgrade öncesi manuel kontrol gerekli."
        )

    lines.extend(
        [
            "",
            "## Sonuç",
            "OK: DA-2E PRE upgrade öncesi DB yedeği ve güvenlik kontrolü geçti.",
        ]
    )

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("OK: DA-2E PRE upgrade öncesi DB yedeği ve güvenlik kontrolü geçti.")
    print(f"REPORT={report_path}")
    print(f"BACKUP_DIR={BACKUP_DIR}")
    print(f"DIALECT={dialect}")
    print("EXISTING_DIGITAL_ARCHIVE_TABLE_COUNT=", len(existing_digital_archive_tables))
