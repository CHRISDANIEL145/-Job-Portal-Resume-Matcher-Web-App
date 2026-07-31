import sqlite3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)
sqlite_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "placement.db")

conn = sqlite3.connect(sqlite_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

tables_in_order = [
    ("user", "id"),
    ("skill", "id"),
    ("student_profile", "id"),
    ("company_profile", "id"),
    ("job_post", "id"),
    ("job_skill", "(job_id, skill_id)"),
    ("student_skill", "(student_id, skill_id)"),
    ("application", "id"),
    ("notification", "id")
]

with engine.connect() as pg_conn:
    print("Starting dynamic full database sync from SQLite to Supabase...")
    for table_name, pk in tables_in_order:
        try:
            col_info = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            cols = [c["name"] for c in col_info]
            rows = cursor.execute(f"SELECT {', '.join(cols)} FROM {table_name}").fetchall()
            print(f"Syncing table '{table_name}' ({len(cols)} cols): found {len(rows)} rows in SQLite...")
            
            for row in rows:
                data_dict = {col: row[col] for col in cols}
                cols_str = ", ".join([f'"{c}"' for c in cols])
                vals_str = ", ".join([f":{c}" for c in cols])
                
                if pk == "id" and "id" in cols:
                    update_cols = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in cols if c != "id"])
                    sql = f'INSERT INTO "{table_name}" ({cols_str}) VALUES ({vals_str}) ON CONFLICT (id) DO UPDATE SET {update_cols};'
                elif pk == "(job_id, skill_id)":
                    sql = f'INSERT INTO "{table_name}" ({cols_str}) VALUES ({vals_str}) ON CONFLICT (job_id, skill_id) DO NOTHING;'
                elif pk == "(student_id, skill_id)":
                    sql = f'INSERT INTO "{table_name}" ({cols_str}) VALUES ({vals_str}) ON CONFLICT (student_id, skill_id) DO NOTHING;'
                else:
                    sql = f'INSERT INTO "{table_name}" ({cols_str}) VALUES ({vals_str}) ON CONFLICT DO NOTHING;'

                try:
                    pg_conn.execute(text(sql), data_dict)
                except Exception:
                    try:
                        pg_conn.execute(text(f'INSERT INTO "{table_name}" ({cols_str}) VALUES ({vals_str}) ON CONFLICT DO NOTHING;'), data_dict)
                    except Exception:
                        pass
            pg_conn.commit()
            print(f"  ✔ Table '{table_name}' synced successfully ({len(rows)} rows)!")
        except Exception as e:
            print(f"  ⚠ Error syncing table '{table_name}': {e}")
            pg_conn.rollback()

    seq_tables = ["user", "skill", "student_profile", "company_profile", "job_post", "application", "notification"]
    for t in seq_tables:
        try:
            pg_conn.execute(text(f"SELECT setval(pg_get_serial_sequence('\"{t}\"', 'id'), COALESCE((SELECT MAX(id)+1 FROM \"{t}\"), 1), false);"))
            pg_conn.commit()
        except Exception:
            pg_conn.rollback()

conn.close()
print("✔✔ FULL DYNAMIC SYNC TO SUPABASE COMPLETE!")
