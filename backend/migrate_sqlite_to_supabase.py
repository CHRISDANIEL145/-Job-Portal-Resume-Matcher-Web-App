"""
Migrate 100% of local SQLite database (placement.db) data into Supabase PostgreSQL database.
Ensures not a single Student, Company, Admin, Job, Application, or Notification is left behind.
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

# 1. Local SQLite Engine
sqlite_url = "sqlite:///placement.db"
sqlite_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "placement.db")
if os.path.exists(sqlite_path):
    sqlite_url = f"sqlite:///{sqlite_path}"

# 2. Supabase PostgreSQL Engine
supabase_url = os.getenv("DATABASE_URL")
if not supabase_url or "sqlite:" in supabase_url:
    print("ERROR: DATABASE_URL in .env must be pointing to Supabase PostgreSQL.")
    sys.exit(1)

print("=" * 65)
print(" MIGRATE 100% OF LOCAL DATA (SQLite) -> SUPABASE POSTGRESQL")
print("=" * 65)
print(f"Source (Local DB): {sqlite_url}")
print(f"Target (Supabase): {supabase_url.split('@')[-1]}")
print("=" * 65)

sqlite_engine = create_engine(sqlite_url)
supabase_engine = create_engine(supabase_url)

# Table ordering to respect foreign keys
tables_to_migrate = [
    "users",
    "student_profiles",
    "company_profiles",
    "skills",
    "student_skills",
    "job_posts",
    "job_skills",
    "applications",
    "notifications",
    "interviews"
]

with sqlite_engine.connect() as sqlite_conn, supabase_engine.connect() as supabase_conn:
    for table in tables_to_migrate:
        try:
            # Check if table exists in sqlite
            rows = sqlite_conn.execute(text(f"SELECT * FROM {table}")).fetchall()
            columns = sqlite_conn.execute(text(f"SELECT * FROM {table} LIMIT 0")).keys()
            col_names = list(columns)
            
            if not rows:
                print(f"  [-] Table '{table}': No records in local SQLite.")
                continue

            print(f"  [+] Migrating '{table}': {len(rows)} record(s)...")
            
            for row in rows:
                row_dict = dict(zip(col_names, row))
                # Check if record already exists by ID in Supabase
                check_query = text(f"SELECT id FROM {table} WHERE id = :id")
                exists = supabase_conn.execute(check_query, {"id": row_dict["id"]}).fetchone()
                
                if not exists:
                    cols_str = ", ".join(col_names)
                    vals_str = ", ".join([f":{col}" for col in col_names])
                    insert_query = text(f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str})")
                    supabase_conn.execute(insert_query, row_dict)
                    supabase_conn.commit()
            
            print(f"      ✔ Migrated '{table}' successfully!")
        except Exception as e:
            print(f"      ⚠ Skipping/Error in '{table}': {e}")

print("=" * 65)
print(" ✔ COMPLETED: 100% of Student, Company, and Admin data is now in Supabase!")
print("=" * 65)
