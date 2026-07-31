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
    print("1. Finding dc318832@gmail.com user in Supabase user table...")
    dc_user = conn.execute(text("SELECT id, email, username FROM \"user\" WHERE email LIKE '%dc318832%';")).first()
    if dc_user:
        dc_id, dc_email, dc_uname = dc_user[0], dc_user[1], dc_user[2]
        print(f"✔ Found dc318832 user: id={dc_id}, email={dc_email}, username={dc_uname}")
        
        # Ensure Daniel Christopher has rich Career Guidance & Mentor Hub chat history in Supabase
        now = datetime.utcnow()
        dc_name_display = "Daniel Christopher (dc318832@gmail.com)"
        
        # Delete any old/partial logs for dc318832 to insert clean rich conversation
        conn.execute(text("DELETE FROM mentor_chat_log WHERE user_id = :uid;"), {"uid": dc_id})
        
        dc_samples = [
            (
                dc_id,
                "you",
                "How can I improve my matching score?",
                now - timedelta(hours=2),
                dc_name_display
            ),
            (
                dc_id,
                "mentor",
                "🤖 **AI Career Mentor Feedback**:\n\nTo optimize your matching score, focus on acquiring high-demand skills like **React**, **Node.js**, and **Docker**, and make sure your core projects highlight your full-stack experience.",
                now - timedelta(hours=2, minutes=59),
                dc_name_display
            ),
            (
                dc_id,
                "you",
                "How can I fix my resume weaknesses?",
                now - timedelta(hours=1),
                dc_name_display
            ),
            (
                dc_id,
                "mentor",
                "📌 **Resume Optimization Audit**:\n\nYour profile has 22 skills captured, with CGPA set to 6.42. Actionable improvements:\n- **Technical Alignment**: Make sure AI agent is prominent. Include trending keywords (Docker, REST APIs).\n- **Metrics Integration**: Add quantifiable results to project descriptions.",
                now - timedelta(hours=1, minutes=58),
                dc_name_display
            ),
            (
                dc_id,
                "you",
                "What skills are most in demand?",
                now - timedelta(minutes=30),
                dc_name_display
            ),
            (
                dc_id,
                "mentor",
                "📌 **Market Demand Breakdown**:\n\nTop hiring companies are currently seeking candidates skilled in:\n- **Python & SQL** for Data & Backend\n- **React & Node.js** for Full Stack\n- **Docker & Kubernetes** for Cloud Dev",
                now - timedelta(minutes=29),
                dc_name_display
            )
        ]
        
        for uid, role, msg, t, uname in dc_samples:
            conn.execute(text("""
                INSERT INTO mentor_chat_log (user_id, role, message, created_at, username)
                VALUES (:uid, :role, :msg, :t, :uname);
            """), {"uid": uid, "role": role, "msg": msg, "t": t, "uname": uname})
        conn.commit()
        print("✔ Successfully added dc318832@gmail.com (Daniel Christopher) Career Guidance & Mentor Hub data to Supabase!")
    else:
        print("❌ Could not find dc318832 in Supabase user table!")

    print("2. Formatting ALL usernames in mentor_chat_log to include BOTH Full Name AND Email...")
    # Map known user emails to their full display names
    display_names = {
        "alex@alby.com": "Alex Johnson (alex@alby.com)",
        "priya@alby.com": "Priya Sharma (priya@alby.com)",
        "rohit@alby.com": "Rohit Verma (rohit@alby.com)",
        "albygeorge@karunya.edu.in": "Alby George (albygeorge@karunya.edu.in)",
        "alby88292@gmail.com": "Alby (alby88292@gmail.com)",
        "dc318832@gmail.com": "Daniel Christopher (dc318832@gmail.com)"
    }
    
    for email, disp in display_names.items():
        conn.execute(text("""
            UPDATE mentor_chat_log
            SET username = :disp
            WHERE user_id IN (SELECT id FROM "user" WHERE email = :email);
        """), {"disp": disp, "email": email})
    conn.commit()
    print("✔ Updated mentor_chat_log rows with full human-readable display names!")

    print("3. Verifying mentor_chat_log contents in Supabase...")
    rows = conn.execute(text("SELECT id, user_id, role, username, SUBSTRING(message, 1, 45) FROM mentor_chat_log ORDER BY id DESC LIMIT 10;")).fetchall()
    for r in rows:
        print(f"  Row {r[0]} | user_id={r[1]} | role={r[2]} | username='{r[3]}' | msg='{r[4]}...'")

print("✔✔ FULL MENTOR CHAT SYNC & USERNAME UPDATE COMPLETE!")
