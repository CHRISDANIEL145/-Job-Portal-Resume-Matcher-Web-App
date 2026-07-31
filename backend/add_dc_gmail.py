import os
import sqlite3
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime
from werkzeug.security import generate_password_hash

load_dotenv()
db_url = os.getenv("DATABASE_URL")

# --- 1. SUPABASE POSTGRESQL ---
if db_url:
    print("1. Adding dc@gmail.com to SUPABASE POSTGRESQL...")
    engine = create_engine(db_url)
    with engine.connect() as conn:
        p_hash = generate_password_hash("12345678")
        now = datetime.utcnow()
        
        row = conn.execute(text("SELECT id FROM \"user\" WHERE email = 'dc@gmail.com'")).first()
        if not row:
            res = conn.execute(text("""
                INSERT INTO "user" (email, password_hash, role, created_at, username)
                VALUES ('dc@gmail.com', :p_hash, 'student', :now, 'Daniel Christopher')
                RETURNING id;
            """), {"p_hash": p_hash, "now": now}).first()
            user_id = res[0]
            print(f"  ✔ Created dc@gmail.com in Supabase (id={user_id})")
        else:
            user_id = row[0]
            conn.execute(text("""
                UPDATE "user"
                SET password_hash = :p_hash, role = 'student', username = 'Daniel Christopher'
                WHERE id = :uid;
            """), {"p_hash": p_hash, "uid": user_id})
            print(f"  ✔ Updated dc@gmail.com in Supabase (id={user_id})")
            
        # Ensure StudentProfile exists
        prof = conn.execute(text("SELECT id FROM student_profile WHERE user_id = :uid;"), {"uid": user_id}).first()
        if not prof:
            prof_res = conn.execute(text("""
                INSERT INTO student_profile (user_id, full_name, gpa, education)
                VALUES (:uid, 'Daniel Christopher', 8.5, 'B.Tech Computer Science & AI')
                RETURNING id;
            """), {"uid": user_id}).first()
            prof_id = prof_res[0]
            print(f"  ✔ Created StudentProfile in Supabase (id={prof_id})")
        else:
            prof_id = prof[0]
            conn.execute(text("""
                UPDATE student_profile
                SET full_name = 'Daniel Christopher'
                WHERE id = :pid;
            """), {"pid": prof_id})
            print(f"  ✔ Verified StudentProfile in Supabase (id={prof_id})")
            
        # Associate skills
        skill_names = ["Python", "React", "Node.js", "SQL", "Machine Learning", "Docker"]
        for sname in skill_names:
            sk = conn.execute(text("SELECT id FROM skill WHERE name = :name;"), {"name": sname}).first()
            if sk:
                sk_id = sk[0]
                try:
                    conn.execute(text("""
                        INSERT INTO student_skill (student_id, skill_id, level)
                        VALUES (:pid, :sid, 'Advanced')
                        ON CONFLICT DO NOTHING;
                    """), {"pid": prof_id, "sid": sk_id})
                except Exception:
                    conn.rollback()
                    
        # Populate username column for all users in Supabase user table
        conn.execute(text("""
            UPDATE "user" u
            SET username = COALESCE(
                (SELECT full_name FROM student_profile sp WHERE sp.user_id = u.id LIMIT 1),
                (SELECT company_name FROM company_profile cp WHERE cp.user_id = u.id LIMIT 1),
                SUBSTRING(u.email FROM 1 FOR POSITION('@' IN u.email) - 1)
            )
            WHERE u.username IS NULL;
        """))
        conn.commit()
        print("  ✔ Populated username column for all users in Supabase")

# --- 2. LOCAL SQLITE DATABASES ---
def add_dc_sqlite(db_path):
    if not os.path.exists(db_path):
        return
    print(f"2. Adding dc@gmail.com to local SQLite: {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    p_hash = generate_password_hash("12345678")
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    cur.execute("SELECT id FROM user WHERE email = 'dc@gmail.com'")
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO user (email, password_hash, role, created_at, username)
            VALUES ('dc@gmail.com', ?, 'student', ?, 'Daniel Christopher')
        """, (p_hash, now))
        user_id = cur.lastrowid
        print(f"  ✔ Created dc@gmail.com in SQLite (id={user_id})")
    else:
        user_id = row[0]
        cur.execute("""
            UPDATE user SET password_hash = ?, role = 'student', username = 'Daniel Christopher'
            WHERE id = ?
        """, (p_hash, user_id))
        print(f"  ✔ Updated dc@gmail.com in SQLite (id={user_id})")
        
    cur.execute("SELECT id FROM student_profile WHERE user_id = ?", (user_id,))
    prof = cur.fetchone()
    if not prof:
        cur.execute("""
            INSERT INTO student_profile (user_id, full_name, gpa, education)
            VALUES (?, 'Daniel Christopher', 8.5, 'B.Tech Computer Science & AI')
        """, (user_id,))
        print("  ✔ Created StudentProfile in SQLite")
    conn.commit()
    conn.close()

add_dc_sqlite("instance/placement.db")
add_dc_sqlite("placement.db")

print("[SUCCESS] dc@gmail.com (Daniel Christopher, password: 12345678) IS LIVE IN SUPABASE AND SQLITE!")
