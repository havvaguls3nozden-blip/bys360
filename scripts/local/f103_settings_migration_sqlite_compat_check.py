from pathlib import Path
import importlib.util
import py_compile

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "migrations" / "versions" / "f103a9d7c2b1_add_settings_foundation_phase1.py"

text = MIGRATION_PATH.read_text(encoding="utf-8-sig")
py_compile.compile(str(MIGRATION_PATH), doraise=True)

required_markers = [
    "_sqlite_column_exists",
    "_bys360_sqlite_ddl_sql",
    "_bys360_sqlite_compatible_statements",
    'op.get_bind().dialect.name == "sqlite"',
    "ADD COLUMN IF NOT EXISTS",
    "DROP COLUMN IF EXISTS",
    'stmt.replace("ADD COLUMN IF NOT EXISTS", "ADD COLUMN")',
    'stmt.replace("DROP COLUMN IF EXISTS", "DROP COLUMN")',
    'sql.replace("id SERIAL PRIMARY KEY", "id INTEGER PRIMARY KEY AUTOINCREMENT")',
    'sql.replace("BOOLEAN NOT NULL DEFAULT FALSE", "INTEGER NOT NULL DEFAULT 0")',
    'sql.replace("BOOLEAN NOT NULL DEFAULT TRUE", "INTEGER NOT NULL DEFAULT 1")',
    'sql.replace("DEFAULT NOW()", "DEFAULT CURRENT_TIMESTAMP")',
]

missing_markers = [marker for marker in required_markers if marker not in text]

if missing_markers:
    raise SystemExit(
        "F103 SQLITE COMPAT FAIL: Gerekli marker eksik:\n"
        + "\n".join(missing_markers)
    )

spec = importlib.util.spec_from_file_location("f103_settings_sqlite_compat", MIGRATION_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class _FakeRows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeDialect:
    name = "sqlite"


class _FakeBind:
    dialect = _FakeDialect()

    def __init__(self, columns):
        self._columns = columns

    def exec_driver_sql(self, _sql):
        return _FakeRows([(index, column) for index, column in enumerate(self._columns)])


class _FakeOp:
    def __init__(self, columns):
        self._bind = _FakeBind(columns)

    def get_bind(self):
        return self._bind


def _convert(stmt, columns):
    module.op = _FakeOp(columns)
    return module._bys360_sqlite_compatible_statements(stmt)


add_stmt = (
    "ALTER TABLE user_menu_permissions "
    "ADD COLUMN IF NOT EXISTS source_type VARCHAR(30) NOT NULL DEFAULT 'user_override'"
)

drop_stmt = "ALTER TABLE user_menu_permissions DROP COLUMN IF EXISTS source_type"

converted_add_missing = _convert(add_stmt, ["id", "user_id"])
if len(converted_add_missing) != 1 or "IF NOT EXISTS" in converted_add_missing[0]:
    raise SystemExit("F103 SQLITE COMPAT FAIL: ADD COLUMN dönüşümü hatalı.")

converted_add_existing = _convert(add_stmt, ["id", "source_type"])
if converted_add_existing != []:
    raise SystemExit("F103 SQLITE COMPAT FAIL: Mevcut kolon için ADD skip edilmeliydi.")

converted_drop_existing = _convert(drop_stmt, ["id", "source_type"])
if len(converted_drop_existing) != 1 or "IF EXISTS" in converted_drop_existing[0]:
    raise SystemExit("F103 SQLITE COMPAT FAIL: DROP COLUMN dönüşümü hatalı.")

converted_drop_missing = _convert(drop_stmt, ["id", "user_id"])
if converted_drop_missing != []:
    raise SystemExit("F103 SQLITE COMPAT FAIL: Eksik kolon için DROP skip edilmeliydi.")

create_stmt = """
CREATE TABLE IF NOT EXISTS role_menu_defaults (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL,
    menu_key VARCHAR(100) NOT NULL,
    is_visible BOOLEAN NOT NULL DEFAULT FALSE,
    source_type VARCHAR(30) NOT NULL DEFAULT 'seed',
    updated_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    note VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_role_menu_default_role_menu UNIQUE (role_name, menu_key)
)
"""

converted_create = _convert(create_stmt, ["id"])

if len(converted_create) != 1:
    raise SystemExit("F103 SQLITE COMPAT FAIL: CREATE TABLE dönüşümü tek SQL üretmeliydi.")

sqlite_create = converted_create[0]

for forbidden in ["SERIAL PRIMARY KEY", "BOOLEAN NOT NULL DEFAULT FALSE", "DEFAULT NOW()"]:
    if forbidden in sqlite_create:
        raise SystemExit(f"F103 SQLITE COMPAT FAIL: CREATE içinde PostgreSQL ifade kaldı: {forbidden}")

for expected in ["INTEGER PRIMARY KEY AUTOINCREMENT", "INTEGER NOT NULL DEFAULT 0", "DEFAULT CURRENT_TIMESTAMP"]:
    if expected not in sqlite_create:
        raise SystemExit(f"F103 SQLITE COMPAT FAIL: CREATE içinde SQLite ifade eksik: {expected}")

print("OK: F103 settings migration SQLite uyumluluk kontrolü geçti.")
print(f"MIGRATION={MIGRATION_PATH}")
