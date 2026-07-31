from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import text
from app.models import Application, CompanyProfile, JobPost, StudentProfile, User, UserRole
from app.extensions import db
from app.services.notifier import create_notification
from app.utils.api import APIError
from app.utils.decorators import role_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/students")
@role_required(UserRole.ADMIN)
def list_students():
    students = StudentProfile.query.all()
    return jsonify(
        [
            {
                "id": s.id,
                "full_name": s.full_name,
                "gpa": s.gpa,
                "education": s.education,
                "skills": [sk.name for sk in s.skills],
            }
            for s in students
        ]
    )


@admin_bp.get("/companies")
@role_required(UserRole.ADMIN)
def list_companies():
    companies = CompanyProfile.query.all()
    return jsonify(
        [{"id": c.id, "company_name": c.company_name, "description": c.description} for c in companies]
    )


@admin_bp.get("/jobs/pending")
@role_required(UserRole.ADMIN)
def pending_jobs():
    jobs = JobPost.query.filter_by(approved=False).all()
    return jsonify(
        [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company.company_name,
                "skills": [s.name for s in j.skills],
                "min_gpa": j.min_gpa,
            }
            for j in jobs
        ]
    )


@admin_bp.patch("/jobs/<int:job_id>/approve")
@role_required(UserRole.ADMIN)
def approve_job(job_id: int):
    job = JobPost.query.get(job_id)
    if not job:
        raise APIError("Job not found", 404, "not_found")

    job.approved = True
    db.session.commit()
    company_user_id = job.company.user_id if job.company else None
    if company_user_id:
        create_notification(
            company_user_id,
            "Job approved",
            f"Your job post for {job.title} has been approved and is now visible to students.",
        )
    return jsonify({"message": "Job approved"})


@admin_bp.get("/analytics")
@role_required(UserRole.ADMIN)
def analytics():
    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    total_jobs = JobPost.query.count()
    approved_jobs = JobPost.query.filter_by(approved=True).count()
    total_apps = Application.query.count()
    shortlisted = Application.query.filter_by(status="shortlisted").count()

    placed_ratio = round((shortlisted / total_students * 100), 2) if total_students else 0

    try:
        user_id = int(get_jwt_identity())
        user_obj = User.query.get(user_id)
        uname = f"Admin {user_obj.username} ({user_obj.email})" if user_obj else f"Admin {user_id}"
        summary_txt = f"{uname} Placement Analytics - Students: {total_students}, Companies: {total_companies}, Total Jobs: {total_jobs}, Approved Jobs: {approved_jobs}, Applications: {total_apps}, Shortlisted: {shortlisted}, Placement Ratio: {placed_ratio}%"
        db.session.execute(text("""
            INSERT INTO placement_analytics (
                username, total_students, total_companies, total_jobs,
                approved_jobs, total_applications, shortlisted_students,
                placement_ratio_percent, summary, created_at
            )
            VALUES (
                :uname, :st, :co, :jobs,
                :appr, :apps, :short,
                :ratio, :summary, CURRENT_TIMESTAMP
            );
        """), {
            "uname": uname,
            "st": total_students,
            "co": total_companies,
            "jobs": total_jobs,
            "appr": approved_jobs,
            "apps": total_apps,
            "short": shortlisted,
            "ratio": placed_ratio,
            "summary": summary_txt
        })
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass

    return jsonify(
        {
            "total_students": total_students,
            "total_companies": total_companies,
            "total_jobs": total_jobs,
            "approved_jobs": approved_jobs,
            "total_applications": total_apps,
            "shortlisted_students": shortlisted,
            "placement_ratio_percent": placed_ratio,
        }
    )
