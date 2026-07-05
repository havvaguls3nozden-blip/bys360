from pathlib import Path
import importlib.util
import py_compile
import re

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "migrations" / "versions" / "b7f4e2a1c9d0_add_ai_support_tables.py"

text = MIGRATION_PATH.read_text(encoding="utf-8-sig")
py_compile.compile(str(MIGRATION_PATH), doraise=True)

required_markers = [
    "_bys360_sqlite_compatible_sql",
    'op.get_bind().dialect.name == "sqlite"',
    "_bys360_sqlite_compatible_sql(stmt)",
]

missing_markers = [marker for marker in required_markers if marker not in text]
if missing_markers:
    raise SystemExit(
        "AI SQLITE COMPAT FAIL: Gerekli marker eksik:\n"
        + "\n".join(missing_markers)
    )

spec = importlib.util.spec_from_file_location("ai_migration_sqlite_compat", MIGRATION_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

samples = [
    """
    CREATE TABLE IF NOT EXISTS ai_request_logs (
        id SERIAL PRIMARY KEY,
        was_masked BOOLEAN NOT NULL DEFAULT TRUE,
        was_user_visible BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_redaction_rules (
        id SERIAL PRIMARY KEY,
        is_active BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP NOT NULL DEFAULT NOW()
    )
    """,
]

bad_tokens = [
    r"\bSERIAL\b",
    r"DEFAULT\s+NOW\(\)",
    r"DEFAULT\s+TRUE\b",
    r"DEFAULT\s+FALSE\b",
]

for sample in samples:
    converted = module._bys360_sqlite_compatible_sql(sample)
    for token in bad_tokens:
        if re.search(token, converted, flags=re.IGNORECASE):
            raise SystemExit(
                "AI SQLITE COMPAT FAIL: SQLite dönüşümünden sonra uyumsuz ifade kaldı:\n"
                + converted
            )

print("OK: AI support migration SQLite uyumluluk kontrolü geçti.")
print(f"MIGRATION={MIGRATION_PATH}")
