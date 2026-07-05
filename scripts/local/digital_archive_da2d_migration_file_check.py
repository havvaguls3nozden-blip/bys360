from pathlib import Path
import ast
import py_compile
import re

from app.digital_archive.model_contract import get_digital_archive_table_names

ROOT = Path(__file__).resolve().parents[2]
VERSIONS_DIR = ROOT / "migrations" / "versions"

migration_files = sorted(
    VERSIONS_DIR.glob("*create_digital_archive_tables.py"),
    key=lambda path: path.stat().st_mtime,
    reverse=True,
)

if not migration_files:
    raise SystemExit("DA-2D FAIL: Dijital Arşiv migration dosyası bulunamadı.")

migration_path = migration_files[0]

# Python kaynak dosyası olarak derlenebiliyor mu?
py_compile.compile(str(migration_path), doraise=True)

text = migration_path.read_text(encoding="utf-8-sig").lstrip("\ufeff")
tree = ast.parse(text, filename=str(migration_path))

expected_tables = set(get_digital_archive_table_names())

create_tables = set()
drop_tables = set()
index_tables = set()
bad_table_ops = []

for node in ast.walk(tree):
    if not isinstance(node, ast.Call):
        continue

    func = node.func
    func_name = func.attr if isinstance(func, ast.Attribute) else ""

    if func_name in {"create_table", "drop_table"}:
        if not node.args or not isinstance(node.args[0], ast.Constant):
            raise SystemExit("DA-2D FAIL: Tablo adı sabit string değil.")

        table_name = node.args[0].value

        if not isinstance(table_name, str):
            raise SystemExit("DA-2D FAIL: Tablo adı string değil.")

        if not table_name.startswith("digital_archive_"):
            bad_table_ops.append(f"{func_name}: {table_name}")

        if func_name == "create_table":
            create_tables.add(table_name)
        else:
            drop_tables.add(table_name)

    if func_name == "create_index":
        if len(node.args) < 2 or not isinstance(node.args[1], ast.Constant):
            raise SystemExit("DA-2D FAIL: create_index tablo adı sabit string değil.")

        table_name = node.args[1].value
        if not isinstance(table_name, str) or not table_name.startswith("digital_archive_"):
            bad_table_ops.append(f"create_index: {table_name}")
        else:
            index_tables.add(table_name)

    if func_name == "drop_index":
        table_name = None
        for keyword in node.keywords:
            if keyword.arg == "table_name" and isinstance(keyword.value, ast.Constant):
                table_name = keyword.value.value

        if not isinstance(table_name, str) or not table_name.startswith("digital_archive_"):
            bad_table_ops.append(f"drop_index: {table_name}")
        else:
            index_tables.add(table_name)

if bad_table_ops:
    raise SystemExit(
        "DA-2D FAIL: digital_archive dışı tablo/index işlemi var:\n"
        + "\n".join(sorted(set(bad_table_ops)))
    )

missing_create = sorted(expected_tables.difference(create_tables))
extra_create = sorted(create_tables.difference(expected_tables))

if missing_create:
    raise SystemExit("DA-2D FAIL: create_table eksik:\n" + "\n".join(missing_create))

if extra_create:
    raise SystemExit("DA-2D FAIL: Sözleşme dışı create_table:\n" + "\n".join(extra_create))

if drop_tables and drop_tables != expected_tables:
    raise SystemExit(
        "DA-2D FAIL: downgrade drop_table seti beklenen tablo ailesiyle eşleşmiyor.\n"
        f"Beklenen={sorted(expected_tables)}\nBulunan={sorted(drop_tables)}"
    )

if "def upgrade():" not in text or "def downgrade():" not in text:
    raise SystemExit("DA-2D FAIL: upgrade/downgrade fonksiyonu eksik.")

upgrade_body = text.split("def upgrade():", 1)[1].split("def downgrade():", 1)[0].lower()

for forbidden in (
    "drop_table",
    "drop_column",
    "alter_column",
    "execute(",
    "bulk_insert",
):
    if forbidden in upgrade_body:
        raise SystemExit(f"DA-2D FAIL: upgrade içinde yasaklı işlem: {forbidden}")

allowed_fk_targets = ("users.id", "organization_units.id", "digital_archive_")
references = re.findall(r'\["([^"]+)"\]', text)
bad_references = [
    ref for ref in references
    if "." in ref and not any(target in ref for target in allowed_fk_targets)
]

if bad_references:
    raise SystemExit(
        "DA-2D FAIL: Beklenmeyen ForeignKey referansı:\n"
        + "\n".join(sorted(set(bad_references)))
    )

if "revision = " not in text or "down_revision = " not in text:
    raise SystemExit("DA-2D FAIL: revision/down_revision eksik.")

print("OK: DA-2D Dijital Arşiv migration dosyası güvenlik kontrolü geçti.")
print(f"MIGRATION={migration_path}")
print("CREATE_TABLES:")
for table_name in sorted(create_tables):
    print(f"- {table_name}")