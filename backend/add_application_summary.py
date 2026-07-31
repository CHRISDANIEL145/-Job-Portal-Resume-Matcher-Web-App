from app import create_app
from app.extensions import db
from app.models import Application, StudentProfile, JobPost, CompanyProfile
from sqlalchemy import text

app = create_app()
with app.app_context():
    print("Connecting to Supabase PostgreSQL...")
    # Add application_summary column if not exists in PostgreSQL
    try:
        db.session.execute(text("ALTER TABLE application ADD COLUMN IF NOT EXISTS application_summary VARCHAR(300);"))
        db.session.commit()
        print("✔ Verified application_summary column in table 'application'")
    except Exception as e:
        db.session.rollback()
        print("Note on ALTER TABLE:", e)

    applications = Application.query.all()
    count = 0
    for app_row in applications:
        student = StudentProfile.query.get(app_row.student_id)
        job = JobPost.query.get(app_row.job_id)
        if student and job and job.company:
            app_row.application_summary = f"{student.full_name} applied for {job.title} at {job.company.company_name}"
            count += 1
            print(f"  + Updated Application #{app_row.id}: {app_row.application_summary}")

    db.session.commit()
    print(f"✔ Successfully updated {count} applications with clear 'X applied for Y at Z' summary in Supabase!")
