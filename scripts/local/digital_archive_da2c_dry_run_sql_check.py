from pathlib import Path
import re

from sqlalchemy import inspect
from sqlalchemy.schema import CreateIndex, CreateTable

from app import create_app, db
from app.digital_archive import models as digital_archive_models  # noqa: F401
from app.digital_archive.model_contract import get_digital_archive_table_names


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.replace("\n", " ").split()).lower()


def _find_forbidden_sql_commands(sql: str) -> list[str]:
    """Gerçek riskli SQL komutlarını yakalar.

    Kolon adları içindeki can_update / updated_at gibi ifadeleri risk saymaz.
    """
    normalized = _normalize_sql(sql)

    forbidden_patterns = {
        "drop table": r"\bdrop\s+table\b",
        "drop column": r"\bdrop\s+column\b",
        "alter table": r"\balter\s+table\b",
        "delete from": r"\bdelete\s+from\b",
        "update statement": r"(^|;)\s*update\s+",
        "insert into": r"(^|;)\s*insert\s+into\b",
        "truncate": r"\btruncate\b",
    }

    hits: list[str] = []
    for label, pattern in forbidden_patterns.items():
        if re.search(pattern, normalized):
            hits.append(label)

    return hits


def main():
    report_dir = Path(r"C:\\bys360\\reports\\digital_archive_da2c_dry_run_fixed_20260705_130423")
    report_dir.mkdir(parents=True, exist_ok=True)

    sql_path = report_dir / "DA2C_DIGITAL_ARCHIVE_CREATE_TABLE_DRY_RUN.sql"
    report_path = report_dir / "DA2C_DRY_RUN_SUMMARY.md"

    app = create_app()

    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)

        existing_tables = set(inspector.get_table_names())
        expected_tables = set(get_digital_archive_table_names())
        metadata_tables = db.metadata.tables

        missing_in_metadata = sorted(expected_tables.difference(metadata_tables.keys()))
        if missing_in_metadata:
            raise SystemExit(
                "DA-2C DRY-RUN FAIL: Metadata içinde eksik Dijital Arşiv tabloları:\n"
                + "\n".join(missing_in_metadata)
            )

        existing_digital_archive_tables = sorted(
            table_name
            for table_name in existing_tables
            if table_name.startswith("digital_archive_")
        )

        create_sql_parts: list[str] = []
        index_sql_parts: list[str] = []

        for table_name in sorted(expected_tables):
            table = metadata_tables[table_name]

            create_sql = str(CreateTable(table).compile(engine)).strip() + ";"
            create_sql_parts.append(create_sql)

            for index in sorted(table.indexes, key=lambda idx: idx.name or ""):
                index_sql = str(CreateIndex(index).compile(engine)).strip() + ";"
                index_sql_parts.append(index_sql)

        full_sql = "\n\n".join(create_sql_parts + index_sql_parts) + "\n"
        sql_path.write_text(full_sql, encoding="utf-8")

        forbidden_hits = _find_forbidden_sql_commands(full_sql)
        if forbidden_hits:
            raise SystemExit(
                "DA-2C DRY-RUN FAIL: SQL içinde yasaklı komut var:\n"
                + "\n".join(forbidden_hits)
            )

        create_table_lines = [
            line.strip()
            for line in full_sql.splitlines()
            if line.strip().upper().startswith("CREATE TABLE")
        ]

        if len(create_table_lines) != len(expected_tables):
            raise SystemExit(
                "DA-2C DRY-RUN FAIL: Beklenen CREATE TABLE sayısı uyuşmuyor. "
                f"Beklenen={len(expected_tables)} Bulunan={len(create_table_lines)}"
            )

        non_digital_create_lines = [
            line for line in create_table_lines if "digital_archive_" not in line
        ]

        if non_digital_create_lines:
            raise SystemExit(
                "DA-2C DRY-RUN FAIL: digital_archive dışı CREATE TABLE bulundu:\n"
                + "\n".join(non_digital_create_lines)
            )

        required_fk_targets = ("users", "organization_units", "digital_archive_")
        suspicious_fk_lines = []
        for line in full_sql.splitlines():
            line_clean = line.strip()
            if "FOREIGN KEY" in line_clean.upper() or "REFERENCES" in line_clean.upper():
                if not any(target in line_clean for target in required_fk_targets):
                    suspicious_fk_lines.append(line_clean)

        if suspicious_fk_lines:
            raise SystemExit(
                "DA-2C DRY-RUN FAIL: Beklenmeyen foreign key hedefi var:\n"
                + "\n".join(suspicious_fk_lines)
            )

        summary = [
            "# BYS360 DA-2C Dijital Arşiv Migration Dry-Run",
            "",
            "Bu rapor veritabanına işlem yapmaz ve migration dosyası oluşturmaz.",
            "",
            f"- Beklenen Dijital Arşiv tablo sayısı: {len(expected_tables)}",
            f"- Mevcut DB içindeki digital_archive_* tablo sayısı: {len(existing_digital_archive_tables)}",
            f"- Üretilen CREATE TABLE sayısı: {len(create_table_lines)}",
            f"- Üretilen index SQL sayısı: {len(index_sql_parts)}",
            "",
            "## Dijital Arşiv tabloları",
        ]

        for table_name in sorted(expected_tables):
            exists_text = "DB'de mevcut" if table_name in existing_tables else "DB'de yok / oluşturulacak"
            summary.append(f"- {table_name}: {exists_text}")

        if existing_digital_archive_tables:
            summary.extend(["", "## DB'de mevcut digital_archive_* tabloları"])
            for table_name in existing_digital_archive_tables:
                summary.append(f"- {table_name}")

        summary.extend(
            [
                "",
                "## Sonuç",
                "",
                "OK: Dry-run SQL yalnızca digital_archive_* tablo ailesini hedefliyor.",
                f"SQL dosyası: {sql_path}",
            ]
        )

        report_path.write_text("\n".join(summary) + "\n", encoding="utf-8")

        print("OK: DA-2C DRY-RUN migration SQL güvenlik kontrolü geçti.")
        print(f"REPORT={report_path}")
        print(f"SQL={sql_path}")
        print("CREATE_TABLE_COUNT=", len(create_table_lines))
        print("DIGITAL_ARCHIVE_TABLES:")
        for table_name in sorted(expected_tables):
            print(f"- {table_name}")


if __name__ == "__main__":
    main()
