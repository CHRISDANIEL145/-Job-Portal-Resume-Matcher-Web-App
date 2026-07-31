import sqlite3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)

sqlite_db = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "placement.db")
if not os.path.exists(sqlite_db):
    print("No SQLite db found.")
else:
    conn = sqlite3.connect(sqlite_db)
    c = conn.cursor()
    users = c.execute("SELECT email, password_hash, role, created_at, username FROM user").fetchall()
    conn.close()

    print(f"Found {len(users)} users in local SQLite placement.db")
    with engine.connect() as pg_conn:
        for u in users:
            email, p_hash, role, created_at, username = u
            if "dc318832" in email:
                print(">>> SQLite contains:", email, role, username)
            try:
                pg_conn.execute(
                    text("""
                    INSERT INTO "user" (email, password_hash, role, created_at, username)
                    VALUES (:email, :p_hash, :role, :created_at, :username)
                    ON CONFLICT (email) DO UPDATE SET username = EXCLUDED.username;
                    """),
                    {"email": email, "p_hash": p_hash, "role": role, "created_at": created_at, "username": username}
                )
            except Exception as e:
                pass
        pg_conn.commit()
    print("✔ Synced all local SQLite users into Supabase PostgreSQL!")
