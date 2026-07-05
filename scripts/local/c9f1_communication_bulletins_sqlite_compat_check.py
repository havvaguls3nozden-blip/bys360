from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "migrations" / "versions" / "c9f1a2b3d4e5_add_communication_phase1_bulletins.py"

text = MIGRATION_PATH.read_text(encoding="utf-8-sig")
py_compile.compile(str(MIGRATION_PATH), doraise=True)

required_markers = [
    "def _sqlite_table_exists(",
    "def _create_table_if_missing(",
    'op.get_bind().dialect.name == "sqlite"',
    "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
    "communication_bulletins",
    "_create_table_if_missing(",
]

missing_markers = [marker for marker in required_markers if marker not in text]

if missing_markers:
    raise SystemExit(
        "C9F1 SQLITE COMPAT FAIL: Gerekli marker eksik:\n"
        + "\n".join(missing_markers)
    )

allowed_helper_call = "op.create_table(table_name, *columns, **kwargs)"
without_allowed_helper = text.replace(allowed_helper_call, "")

if "op.create_table(" in without_allowed_helper:
    raise SystemExit(
        "C9F1 SQLITE COMPAT FAIL: Wrapper dışında op.create_table çağrısı kaldı."
    )

if "_create_table_if_missing(" not in without_allowed_helper:
    raise SystemExit(
        "C9F1 SQLITE COMPAT FAIL: Migration create_table çağrıları wrapper'a dönüşmemiş."
    )

print("OK: C9F1 communication bulletins SQLite mevcut tablo guard kontrolü geçti.")
print(f"MIGRATION={MIGRATION_PATH}")
