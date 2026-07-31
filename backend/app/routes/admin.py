from flask import Blueprint, jsonify
from app.models import Application, CompanyProfile, JobPost, StudentProfile, UserRole
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

    placed_ratio = (shortlisted / total_students * 100) if total_students else 0

    return jsonify(
        {
            "total_students": total_students,
            "total_companies": total_companies,
            "total_jobs": total_jobs,
            "approved_jobs": approved_jobs,
            "total_applications": total_apps,
            "shortlisted_students": shortlisted,
            "placement_ratio_percent": round(placed_ratio, 2),
        }
    )
