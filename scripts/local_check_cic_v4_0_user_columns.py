from sqlalchemy import text
from app import create_app, db

app = create_app()

with app.app_context():
    rows = db.session.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'users'
          AND column_name IN ('birth_date', 'hire_date', 'celebration_opt_out')
        ORDER BY column_name
    """)).fetchall()

    for row in rows:
        print(row.column_name, row.data_type)
