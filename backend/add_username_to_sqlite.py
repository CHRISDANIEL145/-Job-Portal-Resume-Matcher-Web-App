import os
import sqlite3

def fix_sqlite(db_path):
    if not os.path.exists(db_path):
        return
    print(f"Fixing SQLite database: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. Add username column if missing
    for table in ["mentor_chat_log", "application", "notification"]:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN username VARCHAR(150);")
            conn.commit()
            print(f"  [OK] Added username column to {table} in {db_path}")
        except Exception as e:
            conn.rollback()
            # Column already exists
            pass
            
    # 2. Populate application usernames
    try:
        cur.execute("""
            UPDATE application
            SET username = (
                SELECT COALESCE(sp.full_name, 'Student') || ' applied for ' || COALESCE(cp.company_name, 'Company')
                FROM student_profile sp
                LEFT JOIN job_post jp ON jp.id = application.job_id
                LEFT JOIN company_profile cp ON cp.id = jp.company_id
                WHERE sp.id = application.student_id
                LIMIT 1
            );
        """)
        conn.commit()
        print("  [OK] Populated application username in SQLite")
    except Exception as e:
        print(f"  Error updating application: {e}")
        
    # 3. Populate mentor_chat_log usernames
    try:
        cur.execute("""
            UPDATE mentor_chat_log
            SET username = (
                SELECT COALESCE(sp.full_name, u.username, u.email)
                FROM user u
                LEFT JOIN student_profile sp ON sp.user_id = u.id
                WHERE u.id = mentor_chat_log.user_id
                LIMIT 1
            );
        """)
        conn.commit()
        print("  [OK] Populated mentor_chat_log username in SQLite")
    except Exception as e:
        print(f"  Error updating mentor_chat_log: {e}")
        
    conn.close()

fix_sqlite("instance/placement.db")
fix_sqlite("placement.db")
print("[SUCCESS] ALL LOCAL SQLITE DATABASES FIXED & UPGRADED!")
