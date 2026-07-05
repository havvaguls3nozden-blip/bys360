from pathlib import Path
import importlib.util
import py_compile

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "migrations" / "versions" / "a9f2b7c4d001_add_unit_menu_profiles_phase2.py"

text = MIGRATION_PATH.read_text(encoding="utf-8-sig")
py_compile.compile(str(MIGRATION_PATH), doraise=True)

required_markers = [
    "_bys360_sqlite_ddl_sql",
    'op.get_bind().dialect.name == "sqlite"',
    'sql.replace("id SERIAL PRIMARY KEY", "id INTEGER PRIMARY KEY AUTOINCREMENT")',
    'sql.replace("BOOLEAN NOT NULL DEFAULT FALSE", "INTEGER NOT NULL DEFAULT 0")',
    'sql.replace("BOOLEAN NOT NULL DEFAULT TRUE", "INTEGER NOT NULL DEFAULT 1")',
    'sql.replace("DEFAULT NOW()", "DEFAULT CURRENT_TIMESTAMP")',
]

missing_markers = [marker for marker in required_markers if marker not in text]

if missing_markers:
    raise SystemExit(
        "A9F2 SQLITE COMPAT FAIL: Gerekli marker eksik:\n"
        + "\n".join(missing_markers)
    )

spec = importlib.util.spec_from_file_location("a9f2_unit_menu_sqlite_compat", MIGRATION_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

create_stmt = """
CREATE TABLE IF NOT EXISTS unit_menu_profiles (
    id SERIAL PRIMARY KEY,
    unit_name VARCHAR(150) NOT NULL,
    menu_key VARCHAR(100) NOT NULL,
    is_visible BOOLEAN NOT NULL DEFAULT FALSE,
    source_type VARCHAR(30) NOT NULL DEFAULT 'manual',
    updated_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    note VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_unit_menu_profile_unit_menu UNIQUE (unit_name, menu_key)
)
"""

sqlite_create = module._bys360_sqlite_ddl_sql(create_stmt)

for forbidden in ["SERIAL PRIMARY KEY", "BOOLEAN NOT NULL DEFAULT FALSE", "DEFAULT NOW()"]:
    if forbidden in sqlite_create:
        raise SystemExit(f"A9F2 SQLITE COMPAT FAIL: CREATE içinde PostgreSQL ifade kaldı: {forbidden}")

for expected in ["INTEGER PRIMARY KEY AUTOINCREMENT", "INTEGER NOT NULL DEFAULT 0", "DEFAULT CURRENT_TIMESTAMP"]:
    if expected not in sqlite_create:
        raise SystemExit(f"A9F2 SQLITE COMPAT FAIL: CREATE içinde SQLite ifade eksik: {expected}")

print("OK: A9F2 unit menu profiles SQLite uyumluluk kontrolü geçti.")
print(f"MIGRATION={MIGRATION_PATH}")
