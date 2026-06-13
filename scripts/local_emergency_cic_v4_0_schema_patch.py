from sqlalchemy import text
from app import create_app, db

app = create_app()

with app.app_context():
    with db.engine.begin() as conn:
        db_info = conn.execute(text("SELECT current_database() AS db, current_user AS usr")).mappings().first()
        print("DB:", db_info["db"], "| USER:", db_info["usr"])

        conn.execute(text("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS birth_date DATE"))
        conn.execute(text("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS hire_date DATE"))
        conn.execute(text("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS celebration_opt_out BOOLEAN NOT NULL DEFAULT FALSE"))

        rows = conn.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'users'
              AND column_name IN ('birth_date', 'hire_date', 'celebration_opt_out')
            ORDER BY column_name
        """)).mappings().all()

        print("KOLONLAR:")
        for r in rows:
            print("-", r["column_name"], r["data_type"])

        found = {r["column_name"] for r in rows}
        missing = {"birth_date", "hire_date", "celebration_opt_out"} - found
        if missing:
            raise SystemExit("EKSIK KOLON KALDI: " + ", ".join(sorted(missing)))

print("BYS360_CIC_V4_0_EMERGENCY_SCHEMA_PATCH_OK")
