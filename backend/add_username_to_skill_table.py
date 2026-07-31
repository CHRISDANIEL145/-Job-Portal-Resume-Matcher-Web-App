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
    print("1. Adding 'username' column to 'skill' table in Supabase PostgreSQL...")
    conn.execute(text("""
        ALTER TABLE skill ADD COLUMN IF NOT EXISTS username VARCHAR(255);
    """))
    conn.commit()
    print("✔ Column 'username' added to 'skill' table.")

    print("2. Mapping skills to student profiles to populate 'username' column...")
    skills = conn.execute(text("SELECT id, name FROM skill;")).fetchall()
    
    updated_count = 0
    for sk_id, sk_name in skills:
        # Find all students who have this skill
        users_with_skill = conn.execute(text("""
            SELECT sp.full_name, u.email
            FROM student_skill ss
            JOIN student_profile sp ON sp.id = ss.student_id
            JOIN "user" u ON u.id = sp.user_id
            WHERE ss.skill_id = :sk_id
        """), {"sk_id": sk_id}).fetchall()
        
        if users_with_skill:
            unames = [f"{fn} ({em})" for fn, em in users_with_skill]
            uname_str = ", ".join(unames)[:250]
        else:
            # Default fallback for unassigned skills so it's super easy to identify
            uname_str = "Daniel Christopher (dc@gmail.com)"
            
        conn.execute(text("""
            UPDATE skill
            SET username = :uname_str
            WHERE id = :sk_id
        """), {"uname_str": uname_str, "sk_id": sk_id})
        updated_count += 1

    conn.commit()
    print(f"✔ Successfully updated {updated_count} rows in 'skill' table with explicit usernames!")

print("✔✔ 'username' COLUMN IS NOW LIVE AND POPULATED IN THE 'skill' TABLE!")
