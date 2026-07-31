import sys
import os
from werkzeug.security import generate_password_hash

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models import (
    User,
    UserRole,
    StudentProfile,
    CompanyProfile,
    JobPost,
    Application,
    ApplicationStatus,
    Skill,
    Notification,
)

def seed_supabase_data():
    app = create_app()
    with app.app_context():
        print("=" * 65)
        print(" [1/6] Connecting to Database & Creating Tables...")
        print("=" * 65)
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        db.create_all()
        print("✔ All tables created successfully!")

        print("\n [2/6] Seeding Skills...")
        skills_map = {}
        skill_names = [
            "Python", "React", "Flask", "SQL", "Machine Learning",
            "Tailwind CSS", "Data Structures", "REST API", "Git", "Docker"
        ]
        for name in skill_names:
            skill = Skill.query.filter_by(name=name).first()
            if not skill:
                skill = Skill(name=name)
                db.session.add(skill)
                db.session.flush()
            skills_map[name] = skill
        db.session.commit()
        print(f"✔ {len(skills_map)} skills stored in Supabase.")

        print("\n [3/6] Seeding Users (Admin, Companies, Students)...")
        # 1. Admin User
        admin_email = "admin@alby.com"
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                email=admin_email,
                password_hash=generate_password_hash("password123"),
                role=UserRole.ADMIN.value
            )
            db.session.add(admin_user)
            db.session.flush()
            print(f"  + Added Admin: {admin_email} (password: password123)")

        # 2. Company Users
        company_data = [
            {
                "email": "recruiter@techcorp.com",
                "name": "TechCorp Global",
                "desc": "Leading tech corporation in AI & Cloud solutions.",
                "url": "https://www.techcorp.example.com"
            },
            {
                "email": "hiring@innovateai.com",
                "name": "Innovate AI Labs",
                "desc": "Next-generation AI research and development laboratory.",
                "url": "https://www.innovateai.example.com"
            }
        ]
        companies_map = {}
        for c in company_data:
            user = User.query.filter_by(email=c["email"]).first()
            if not user:
                user = User(
                    email=c["email"],
                    password_hash=generate_password_hash("password123"),
                    role=UserRole.COMPANY.value
                )
                db.session.add(user)
                db.session.flush()
            profile = CompanyProfile.query.filter_by(user_id=user.id).first()
            if not profile:
                profile = CompanyProfile(
                    user_id=user.id,
                    company_name=c["name"],
                    description=c["desc"],
                    website_url=c["url"]
                )
                db.session.add(profile)
                db.session.flush()
                print(f"  + Added Company: {c['name']} ({c['email']})")
            companies_map[c["name"]] = profile

        # 3. Student Users
        student_data = [
            {
                "email": "alex@alby.com",
                "name": "Alex Johnson",
                "gpa": 3.85,
                "edu": "B.Tech Computer Science",
                "skills": ["Python", "React", "Flask", "SQL", "Git"]
            },
            {
                "email": "priya@alby.com",
                "name": "Priya Sharma",
                "gpa": 3.92,
                "edu": "B.Tech Artificial Intelligence & Data Science",
                "skills": ["Python", "Machine Learning", "SQL", "Data Structures", "Docker"]
            },
            {
                "email": "rohit@alby.com",
                "name": "Rohit Verma",
                "gpa": 3.40,
                "edu": "B.Tech Information Technology",
                "skills": ["React", "Tailwind CSS", "REST API", "Git"]
            }
        ]
        students_map = {}
        for s in student_data:
            user = User.query.filter_by(email=s["email"]).first()
            if not user:
                user = User(
                    email=s["email"],
                    password_hash=generate_password_hash("password123"),
                    role=UserRole.STUDENT.value
                )
                db.session.add(user)
                db.session.flush()
            profile = StudentProfile.query.filter_by(user_id=user.id).first()
            if not profile:
                profile = StudentProfile(
                    user_id=user.id,
                    full_name=s["name"],
                    gpa=s["gpa"],
                    education=s["edu"]
                )
                for sk_name in s["skills"]:
                    if sk_name in skills_map and skills_map[sk_name] not in profile.skills:
                        profile.skills.append(skills_map[sk_name])
                db.session.add(profile)
                db.session.flush()
                print(f"  + Added Student: {s['name']} ({s['email']})")
            students_map[s["name"]] = profile

        db.session.commit()
        print("✔ Admin, Companies, and Students stored in Supabase.")

        print("\n [4/6] Seeding Job Posts...")
        job_defs = [
            {
                "company": "TechCorp Global",
                "title": "Frontend React Developer",
                "desc": "Seeking a talented Frontend Developer proficient in React, Tailwind CSS, and REST API integration.",
                "gpa": 3.2,
                "skills": ["React", "Tailwind CSS", "REST API", "Git"]
            },
            {
                "company": "Innovate AI Labs",
                "title": "AI / ML Backend Engineer",
                "desc": "Join our AI systems group to develop scalable Python machine learning pipelines and microservices.",
                "gpa": 3.5,
                "skills": ["Python", "Machine Learning", "SQL", "Docker"]
            },
            {
                "company": "TechCorp Global",
                "title": "Full Stack Software Engineer",
                "desc": "Build end-to-end web applications with modern React frontend and Flask/SQLAlchemy backend.",
                "gpa": 3.6,
                "skills": ["Python", "React", "Flask", "SQL", "Data Structures"]
            }
        ]
        jobs_map = {}
        for jd in job_defs:
            comp_profile = companies_map.get(jd["company"])
            if not comp_profile:
                continue
            job = JobPost.query.filter_by(company_id=comp_profile.id, title=jd["title"]).first()
            if not job:
                job = JobPost(
                    company_id=comp_profile.id,
                    title=jd["title"],
                    description=jd["desc"],
                    min_gpa=jd["gpa"],
                    approved=True
                )
                for sk_name in jd["skills"]:
                    if sk_name in skills_map and skills_map[sk_name] not in job.skills:
                        job.skills.append(skills_map[sk_name])
                db.session.add(job)
                db.session.flush()
                print(f"  + Added Job: '{jd['title']}' at {jd['company']}")
            jobs_map[jd["title"]] = job
        db.session.commit()
        print("✔ All Job Posts stored in Supabase.")

        print("\n [5/6] Seeding Applications...")
        app_defs = [
            {
                "student": "Alex Johnson",
                "job": "Full Stack Software Engineer",
                "score": 92.5,
                "status": ApplicationStatus.SHORTLISTED.value
            },
            {
                "student": "Alex Johnson",
                "job": "Frontend React Developer",
                "score": 88.0,
                "status": ApplicationStatus.APPLIED.value
            },
            {
                "student": "Priya Sharma",
                "job": "AI / ML Backend Engineer",
                "score": 96.4,
                "status": ApplicationStatus.SHORTLISTED.value
            },
            {
                "student": "Rohit Verma",
                "job": "Frontend React Developer",
                "score": 85.0,
                "status": ApplicationStatus.APPLIED.value
            }
        ]
        for ad in app_defs:
            s_prof = students_map.get(ad["student"])
            j_post = jobs_map.get(ad["job"])
            if s_prof and j_post:
                existing_app = Application.query.filter_by(student_id=s_prof.id, job_id=j_post.id).first()
                if not existing_app:
                    application = Application(
                        student_id=s_prof.id,
                        job_id=j_post.id,
                        matching_score=ad["score"],
                        status=ad["status"]
                    )
                    db.session.add(application)
                    print(f"  + Added Application: {ad['student']} -> {ad['job']} (score: {ad['score']})")
        db.session.commit()
        print("✔ Applications stored in Supabase.")

        print("\n [6/6] Seeding Notifications...")
        for name, s_prof in students_map.items():
            if not Notification.query.filter_by(user_id=s_prof.user_id).first():
                notif = Notification(
                    user_id=s_prof.user_id,
                    title="Welcome to ALBY!",
                    message="Your student profile is active. Browse new job postings and practice AI interviews."
                )
                db.session.add(notif)
        db.session.commit()
        print("✔ Notifications stored in Supabase.")

        print("\n" + "=" * 65)
        print(" ✔ COMPLETE: All ALBY Data (Student, Company, Admin) stored!")
        print("             You can now see ALL data in your Supabase Dashboard.")
        print("=" * 65)

if __name__ == "__main__":
    seed_supabase_data()
