from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import or_
from app.extensions import db
from app.models import Application, ApplicationStatus, JobPost, StudentProfile, User, UserRole
from app.services.matching import auto_shortlist, final_matching_score
from app.services.notifier import create_notification
from app.utils.api import APIError, serialize_paginated
from app.utils.decorators import role_required
from app.utils.validators import parse_optional_gpa, parse_pagination_args

job_bp = Blueprint("job", __name__)


@job_bp.get("")
@role_required(UserRole.STUDENT, UserRole.ADMIN)
def list_jobs():
    user_id = int(get_jwt_identity())
    student_profile = StudentProfile.query.filter_by(user_id=user_id).first()
    student_skill_names = [s.name for s in student_profile.skills] if student_profile else []
    student_gpa = student_profile.gpa if student_profile else None

    page, per_page = parse_pagination_args(request)
    search = (request.args.get("search") or "").strip()
    skill = (request.args.get("skill") or "").strip().lower()
    max_gpa = parse_optional_gpa(request.args.get("max_gpa"))

    query = JobPost.query.filter_by(approved=True)

    if search:
        like = f"%{search}%"
        query = query.filter(or_(JobPost.title.ilike(like), JobPost.description.ilike(like)))
    if skill:
        query = query.filter(JobPost.skills.any(name=skill))
    if max_gpa is not None:
        query = query.filter(or_(JobPost.min_gpa.is_(None), JobPost.min_gpa <= max_gpa))

    query = query.order_by(JobPost.created_at.desc())

    def serialize_job(job: JobPost):
        gpa_eligible = True
        if student_gpa is not None and job.min_gpa is not None:
            gpa_eligible = float(student_gpa) + 0.15 >= float(job.min_gpa)

        payload = {
            "id": job.id,
            "job_id": job.id,
            "title": job.title,
            "description": job.description,
            "min_gpa": job.min_gpa,
            "company": job.company.company_name,
            "company_name": job.company.company_name,
            "company_id": job.company.id,
            "skills": [s.name for s in job.skills],
            "required_skills": [s.name for s in job.skills],
            "gpa_eligible": gpa_eligible,
            "apply_url": job.company.website_url if job.company.website_url else None,
        }



        if student_profile:
            payload["matching_score"] = final_matching_score(
                student_skill_names,
                [s.name for s in job.skills],
                student_gpa,
                job.min_gpa,
            )
        return payload

    payload = serialize_paginated(
        query,
        serialize_job,
        page,
        per_page,
    )
    return jsonify(payload)


@job_bp.post("/<int:job_id>/apply")
@role_required(UserRole.STUDENT)
def apply_job(job_id: int):
    user_id = int(get_jwt_identity())
    student = StudentProfile.query.filter_by(user_id=user_id).first()
    job = JobPost.query.filter_by(id=job_id, approved=True).first()

    if not student:
        raise APIError("Create student profile first", 400, "missing_profile")
    if not job:
        raise APIError("Job not found or not approved", 404, "not_found")

    existing = Application.query.filter_by(student_id=student.id, job_id=job.id).first()
    if existing:
        raise APIError("Already applied", 409, "conflict")

    score = final_matching_score(
        [s.name for s in student.skills],
        [s.name for s in job.skills],
        student.gpa,
        job.min_gpa,
    )

    shortlisted = auto_shortlist(score)
    status = ApplicationStatus.SHORTLISTED.value if shortlisted else ApplicationStatus.APPLIED.value

    app = Application(
        student_id=student.id,
        job_id=job.id,
        matching_score=score,
        status=status,
        application_summary=f"{student.full_name} applied for {job.title} at {job.company.company_name}",
    )
    db.session.add(app)
    db.session.commit()

    student_user = User.query.get(student.user_id)
    company_user = User.query.get(job.company.user_id)
    if shortlisted:
        create_notification(
            student_user.id,
            "Shortlisted",
            f"You have been shortlisted for {job.title} at {job.company.company_name}",
        )
        if company_user:
            create_notification(
                company_user.id,
                "New shortlist",
                f"{student.full_name} was shortlisted for {job.title} at {job.company.company_name}",
            )
    else:
        create_notification(
            student_user.id,
            "Application Received",
            f"Your application for {job.title} was submitted with score {score}",
        )
        if company_user:
            create_notification(
                company_user.id,
                "New applicant",
                f"{student.full_name} applied for {job.title} at {job.company.company_name}",
            )

    return jsonify({
        "message": "Application submitted",
        "matching_score": score,
        "status": status,
        "apply_url": job.company.website_url if job.company.website_url else None
    }), 201
