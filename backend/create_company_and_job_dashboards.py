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
    print("1. Adding 'username' column to 'company_profile' and 'job_post' in Supabase PostgreSQL...")
    conn.execute(text("ALTER TABLE company_profile ADD COLUMN IF NOT EXISTS username VARCHAR(255);"))
    conn.execute(text("ALTER TABLE job_post ADD COLUMN IF NOT EXISTS username VARCHAR(255);"))
    conn.commit()

    print("2. Creating 'company_profile_dashboard' table in Supabase PostgreSQL...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS company_profile_dashboard (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            username VARCHAR(255) NOT NULL,
            company_name VARCHAR(255) NOT NULL,
            description TEXT,
            website_url VARCHAR(500),
            jobs_posted_count INTEGER DEFAULT 0,
            summary TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))
    conn.commit()

    print("3. Creating 'post_job_opening' table (and view alias 'post_job_opening_dashboard') in Supabase PostgreSQL...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS post_job_opening (
            id SERIAL PRIMARY KEY,
            company_id INTEGER,
            username VARCHAR(255) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            min_gpa FLOAT,
            approved BOOLEAN DEFAULT FALSE,
            skills_required VARCHAR(500),
            summary TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """))
    conn.commit()

    try:
        conn.execute(text("""
            CREATE OR REPLACE VIEW post_job_opening_dashboard AS
            SELECT * FROM post_job_opening;
        """))
        conn.commit()
    except Exception as e:
        print("Note on view:", e)

    print("4. Populating company_profile username and company_profile_dashboard...")
    # Fetch all company profiles and their user email
    comps = conn.execute(text("""
        SELECT cp.id, cp.user_id, cp.company_name, cp.description, cp.website_url, cp.created_at, u.email, u.username
        FROM company_profile cp
        JOIN "user" u ON u.id = cp.user_id
    """)).fetchall()

    conn.execute(text("DELETE FROM company_profile_dashboard;"))
    conn.commit()

    comp_map = {} # company_id -> username
    comp_count = 0
    for cid, uid, cname, desc, web, cat, uemail, uuname in comps:
        uname_str = f"{cname} ({uemail})"
        comp_map[cid] = uname_str
        
        # update company_profile
        conn.execute(text("UPDATE company_profile SET username = :uname WHERE id = :cid;"), {"uname": uname_str, "cid": cid})
        
        # count jobs
        jcount = conn.execute(text("SELECT COUNT(*) FROM job_post WHERE company_id = :cid;"), {"cid": cid}).scalar() or 0
        summary_txt = f"{uname_str} Company Profile - Website: {web or 'N/A'} | {jcount} jobs posted. {desc or ''}"[:280]
        
        conn.execute(text("""
            INSERT INTO company_profile_dashboard (
                user_id, username, company_name, description, website_url, jobs_posted_count, summary, created_at
            )
            VALUES (:uid, :uname, :cname, :desc, :web, :jcount, :summary, :cat);
        """), {
            "uid": uid,
            "uname": uname_str,
            "cname": cname,
            "desc": desc,
            "web": web,
            "jcount": jcount,
            "summary": summary_txt,
            "cat": cat or datetime.utcnow()
        })
        comp_count += 1

    print("5. Populating job_post username and post_job_opening table...")
    jobs = conn.execute(text("""
        SELECT jp.id, jp.company_id, jp.title, jp.description, jp.min_gpa, jp.approved, jp.created_at
        FROM job_post jp
    """)).fetchall()

    conn.execute(text("DELETE FROM post_job_opening;"))
    conn.commit()

    job_count = 0
    for jid, cid, title, desc, min_gpa, apprv, cat in jobs:
        uname_str = comp_map.get(cid, "Acme Corp (test_company_99@test.com)")
        
        # update job_post
        conn.execute(text("UPDATE job_post SET username = :uname WHERE id = :jid;"), {"uname": uname_str, "jid": jid})
        
        # fetch skills for this job
        j_skills = conn.execute(text("""
            SELECT s.name
            FROM job_skill js
            JOIN skill s ON s.id = js.skill_id
            WHERE js.job_id = :jid
        """), {"jid": jid}).fetchall()
        sk_str = ", ".join([sk[0] for sk in j_skills]) or "python, sql, git"
        
        status_str = "Approved" if apprv else "Pending Review"
        summary_txt = f"{uname_str} posted job opening: '{title}' - Skills: {sk_str} [{status_str}]"[:280]
        
        conn.execute(text("""
            INSERT INTO post_job_opening (
                company_id, username, title, description, min_gpa, approved, skills_required, summary, created_at
            )
            VALUES (:cid, :uname, :title, :desc, :gpa, :appr, :skills, :summary, :cat);
        """), {
            "cid": cid,
            "uname": uname_str,
            "title": title,
            "desc": desc,
            "gpa": min_gpa,
            "appr": apprv,
            "skills": sk_str,
            "summary": summary_txt,
            "cat": cat or datetime.utcnow()
        })
        job_count += 1

    conn.commit()
    print(f"✔ Successfully populated {comp_count} rows in 'company_profile_dashboard' and {job_count} rows in 'post_job_opening'!")

print("✔✔ COMPANY PROFILE AND POST JOB OPENING TABLES ARE NOW LIVE IN SUPABASE!")
