from sqlalchemy import text
from app import create_app, db

app = create_app()

with app.app_context():
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS hire_date DATE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS celebration_opt_out BOOLEAN NOT NULL DEFAULT FALSE"
    ]

    for stmt in statements:
        db.session.execute(text(stmt))

    db.session.commit()
    print("BYS360_CIC_V4_0_LOCAL_SCHEMA_PATCH_OK")
