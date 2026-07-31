import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not found!")
    exit(1)

engine = create_engine(db_url)

with engine.connect() as conn:
    print("Adding username column to mentor_chat_log, application, and notification in Supabase PostgreSQL...")
    
    for table in ["mentor_chat_log", "application", "notification"]:
        try:
            conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS username VARCHAR(150);'))
            conn.commit()
            print(f"✔ Verified username column on {table}")
        except Exception as e:
            conn.rollback()

    # 1. Populate mentor_chat_log with actual user full names (e.g., Daniel Christopher)
    conn.execute(text("""
        UPDATE mentor_chat_log m
        SET username = (
            SELECT COALESCE(sp.full_name, u.username, u.email)
            FROM "user" u
            LEFT JOIN student_profile sp ON sp.user_id = u.id
            WHERE u.id = m.user_id
            LIMIT 1
        );
    """))
    conn.commit()
    print("✔ Populated username in mentor_chat_log with full names (e.g. Daniel Christopher)")

    # 2. Populate application with descriptive usernames ("Daniel Christopher applied for TechCorp")
    conn.execute(text("""
        UPDATE application a
        SET username = (
            SELECT COALESCE(sp.full_name, 'Student') || ' applied for ' || COALESCE(cp.company_name, 'Company')
            FROM student_profile sp
            LEFT JOIN job_post jp ON jp.id = a.job_id
            LEFT JOIN company_profile cp ON cp.id = jp.company_id
            WHERE sp.id = a.student_id
            LIMIT 1
        );
    """))
    conn.commit()
    print("✔ Populated username in application (e.g. 'Daniel Christopher applied for TechCorp')")

    # 3. Populate notification with user names
    conn.execute(text("""
        UPDATE notification n
        SET username = (
            SELECT COALESCE(sp.full_name, cp.company_name, u.username, u.email)
            FROM "user" u
            LEFT JOIN student_profile sp ON sp.user_id = u.id
            LEFT JOIN company_profile cp ON cp.user_id = u.id
            WHERE u.id = n.user_id
            LIMIT 1
        );
    """))
    conn.commit()
    print("✔ Populated username in notification")

print("✔✔ ALL SUPABASE TABLES NOW FEATURE EXPLICIT HUMAN-READABLE USER NAMES!")
