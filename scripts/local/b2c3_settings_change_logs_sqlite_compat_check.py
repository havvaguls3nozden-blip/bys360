from pathlib import Path
import importlib.util
import py_compile

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "migrations" / "versions" / "b2c3d4e5f6a7_add_settings_change_logs_phase3.py"

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
        "B2C3 SQLITE COMPAT FAIL: Gerekli marker eksik:\n"
        + "\n".join(missing_markers)
    )

spec = importlib.util.spec_from_file_location("b2c3_settings_change_logs_sqlite_compat", MIGRATION_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

create_stmt = """
CREATE TABLE IF NOT EXISTS settings_change_logs (
    id SERIAL PRIMARY KEY,
    actor_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    target_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    target_role_name VARCHAR(50) NULL,
    target_unit_name VARCHAR(150) NULL,
    change_scope VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    summary VARCHAR(255) NULL,
    previous_state_json TEXT NULL,
    new_state_json TEXT NULL,
    reverted_from_log_id INTEGER NULL REFERENCES settings_change_logs(id) ON DELETE SET NULL,
    is_rollback BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
)
"""

sqlite_create = module._bys360_sqlite_ddl_sql(create_stmt)

for forbidden in ["SERIAL PRIMARY KEY", "BOOLEAN NOT NULL DEFAULT FALSE", "DEFAULT NOW()"]:
    if forbidden in sqlite_create:
        raise SystemExit(f"B2C3 SQLITE COMPAT FAIL: CREATE içinde PostgreSQL ifade kaldı: {forbidden}")

for expected in ["INTEGER PRIMARY KEY AUTOINCREMENT", "INTEGER NOT NULL DEFAULT 0", "DEFAULT CURRENT_TIMESTAMP"]:
    if expected not in sqlite_create:
        raise SystemExit(f"B2C3 SQLITE COMPAT FAIL: CREATE içinde SQLite ifade eksik: {expected}")

print("OK: B2C3 settings change logs SQLite uyumluluk kontrolü geçti.")
print(f"MIGRATION={MIGRATION_PATH}")
