import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not found!")
    exit(1)

engine = create_engine(db_url)

with engine.connect() as conn:
    print("Creating mentor_chat_log table in Supabase PostgreSQL...")
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS mentor_chat_log (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
        role VARCHAR(20) NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
    );
    """))
    conn.commit()
    print("✔ Table mentor_chat_log created successfully!")

    # Find Daniel Christopher (or any student user) to seed initial mentor hub history
    res = conn.execute(text("SELECT id, email FROM \"user\" WHERE role = 'student' ORDER BY id ASC LIMIT 5;")).fetchall()
    print(f"Found {len(res)} student users to seed initial Career Guidance & Mentor Hub data...")

    for u in res:
        uid, email = u[0], u[1]
        now = datetime.utcnow()
        samples = [
            (uid, "you", "How can I improve my matching score?", now - timedelta(hours=3)),
            (uid, "mentor", "🤖 **AI Career Mentor Feedback**:\n\nTo optimize your matching score, focus on acquiring high-demand skills like **React** and **Docker**, and ensure your GPA is accurately listed on your profile.", now - timedelta(hours=3, minutes=59)),
            (uid, "you", "What skills are most in demand?", now - timedelta(hours=1)),
            (uid, "mentor", "📌 **Market Demand Breakdown**:\n\nTop hiring companies are currently seeking candidates skilled in:\n- **Python & SQL** for Data & Backend\n- **React & Node.js** for Full Stack\n- **Docker & Kubernetes** for Cloud Dev", now - timedelta(hours=1, minutes=58))
        ]
        for s_uid, s_role, s_msg, s_time in samples:
            conn.execute(text("""
                INSERT INTO mentor_chat_log (user_id, role, message, created_at)
                VALUES (:uid, :role, :msg, :time)
                ON CONFLICT DO NOTHING;
            """), {"uid": s_uid, "role": s_role, "msg": s_msg, "time": s_time})
    conn.commit()
    print("✔ Seeded initial Career Guidance & Mentor Hub messages into Supabase!")
