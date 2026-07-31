from app import create_app
from app.extensions import db
from sqlalchemy import text
import sqlite3
import os

app = create_app()

# 1. Update SQLite
sqlite_paths = [
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "placement.db"),
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "placement.db")
]
for p in sqlite_paths:
    if os.path.exists(p):
        conn = sqlite3.connect(p)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN username VARCHAR(80);")
            conn.commit()
            print(f"✔ Added username column to SQLite in {p}")
        except Exception as e:
            print(f"Note on SQLite ALTER: {e}")
        conn.close()

# 2. Update Supabase PostgreSQL if connected
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS username VARCHAR(80);"))
        db.session.commit()
        print("✔ Added username column to Supabase PostgreSQL table 'user'")
    except Exception as e:
        db.session.rollback()
        print("Note on Supabase ALTER:", e)
print("✔ Username column migration complete!")
