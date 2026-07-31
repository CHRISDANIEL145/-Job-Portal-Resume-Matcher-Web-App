import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not found!")
    exit(1)

engine = create_engine(db_url)

with engine.connect() as conn:
    print("1. Creating peer_comparison table in Supabase PostgreSQL...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS peer_comparison (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
            username VARCHAR(255) NOT NULL,
            student_gpa FLOAT,
            student_skills_count INTEGER,
            cohort_avg_gpa FLOAT,
            cohort_avg_skills FLOAT,
            gpa_percentile FLOAT,
            skills_percentile FLOAT,
            comparison_summary TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))
    conn.commit()
    print("✔ Created peer_comparison table in Supabase PostgreSQL")

    # Also create a view/alias peer_comparison_dashboard in case user looks for that exact name in Table Editor
    try:
        conn.execute(text("""
            CREATE OR REPLACE VIEW peer_comparison_dashboard AS
            SELECT * FROM peer_comparison;
        """))
        conn.commit()
        print("✔ Created peer_comparison_dashboard view alias in Supabase PostgreSQL")
    except Exception as e:
        print("Note on view:", e)

    print("2. Populating peer_comparison table for all student profiles in Supabase...")
    # Get all student profiles and calculate cohort stats
    profiles = conn.execute(text("""
        SELECT sp.id, sp.user_id, sp.full_name, sp.gpa, u.email,
               (SELECT COUNT(*) FROM student_skill ss WHERE ss.student_id = sp.id) as skill_count
        FROM student_profile sp
        JOIN "user" u ON u.id = sp.user_id
    """)).fetchall()

    if profiles:
        gpas = [float(p[3] or 7.0) for p in profiles]
        skill_counts = [int(p[5] or 0) for p in profiles]
        avg_gpa = round(sum(gpas) / len(gpas), 2)
        avg_skills = round(sum(skill_counts) / len(skill_counts), 1)

        # Clear existing rows to prevent duplicates on rerun
        conn.execute(text("DELETE FROM peer_comparison;"))
        conn.commit()

        for p in profiles:
            sp_id, user_id, full_name, gpa, email, skill_count = p
            gpa_val = float(gpa or 7.0)
            
            peers_below_gpa = sum(1 for g in gpas if g <= gpa_val)
            gpa_pct = max(5, round((peers_below_gpa / len(gpas)) * 100))
            
            peers_below_skills = sum(1 for sc in skill_counts if sc <= skill_count)
            skill_pct = max(5, round((peers_below_skills / len(skill_counts)) * 100))
            
            # Mention clear username with email
            display_name = f"{full_name} ({email})"
            
            notes = []
            if gpa_val >= avg_gpa:
                notes.append(f"{full_name}'s GPA ({gpa_val}) is above the cohort average of {avg_gpa}.")
            else:
                notes.append(f"{full_name}'s GPA ({gpa_val}) is below the cohort average of {avg_gpa}.")
                
            if skill_count >= avg_skills:
                notes.append(f"Skill breadth ({skill_count} skills) puts {full_name} ahead of the cohort average ({avg_skills} skills).")
            else:
                notes.append(f"Has {skill_count} skills compared to the cohort average of {avg_skills} skills.")
                
            summary_text = " ".join(notes)
            
            conn.execute(text("""
                INSERT INTO peer_comparison (
                    user_id, username, student_gpa, student_skills_count,
                    cohort_avg_gpa, cohort_avg_skills, gpa_percentile, skills_percentile,
                    comparison_summary, created_at
                )
                VALUES (
                    :uid, :uname, :gpa, :scount,
                    :avg_gpa, :avg_skills, :gpa_pct, :skill_pct,
                    :summary, CURRENT_TIMESTAMP
                );
            """), {
                "uid": user_id,
                "uname": display_name,
                "gpa": gpa_val,
                "scount": skill_count,
                "avg_gpa": avg_gpa,
                "avg_skills": avg_skills,
                "gpa_pct": gpa_pct,
                "skill_pct": skill_pct,
                "summary": summary_text
            })
        conn.commit()
        print(f"✔ Successfully populated {len(profiles)} rows in peer_comparison table with explicit usernames!")

print("✔✔ PEER COMPARISON DASHBOARD TABLE IS COMPLETE AND LIVE IN SUPABASE!")
