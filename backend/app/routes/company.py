from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy import text
from app.extensions import db
from app.models import CompanyProfile, JobPost, Skill, User, UserRole
from app.utils.api import APIError, serialize_paginated
from app.utils.decorators import role_required
from app.utils.validators import parse_optional_gpa, parse_pagination_args, parse_skill_list

company_bp = Blueprint("company", __name__)


def _set_job_skills(job: JobPost, skills: list[str]):
    job.skills = []
    for skill_name in skills:
        skill = Skill.query.filter_by(name=skill_name.lower()).first()
        if not skill:
            skill = Skill(name=skill_name.lower())
            db.session.add(skill)
            db.session.flush()
        job.skills.append(skill)


@company_bp.get("")
@role_required(UserRole.STUDENT, UserRole.ADMIN)
def list_companies_for_students():
    companies = CompanyProfile.query.order_by(CompanyProfile.created_at.desc()).all()
    return jsonify(
        [
            {
                "id": company.id,
                "company_name": company.company_name,
                "description": company.description,
                "total_jobs": len(company.jobs),
                "approved_jobs": sum(1 for job in company.jobs if job.approved),
            }
            for company in companies
        ]
    )


@company_bp.post("/profile")
@role_required(UserRole.COMPANY)
def upsert_company_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    company_name = (data.get("company_name") or "").strip()
    description = (data.get("description") or "").strip() or None
    website_url = (data.get("website_url") or "").strip() or None

    if not company_name:
        raise APIError("company_name required", 422, "validation_error")


    profile = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = CompanyProfile(user_id=user_id, company_name=company_name)
        db.session.add(profile)

    profile.company_name = company_name
    profile.description = description
    profile.website_url = website_url
    db.session.commit()

    try:
        user_obj = User.query.get(user_id)
        uname = f"{company_name} ({user_obj.email})" if user_obj else company_name
        jcount = len(profile.jobs) if hasattr(profile, 'jobs') else 0
        summary_txt = f"{uname} Company Profile - Website: {website_url or 'N/A'} | {jcount} jobs posted. {description or ''}"[:280]
        db.session.execute(text("""
            UPDATE company_profile SET username = :uname WHERE id = :cid;
        """), {"uname": uname, "cid": profile.id})
        db.session.execute(text("""
            INSERT INTO company_profile_dashboard (
                user_id, username, company_name, description, website_url, jobs_posted_count, summary, created_at
            )
            VALUES (:uid, :uname, :cname, :desc, :web, :jcount, :summary, CURRENT_TIMESTAMP);
        """), {
            "uid": user_id,
            "uname": uname,
            "cname": company_name,
            "desc": description,
            "web": website_url,
            "jcount": jcount,
            "summary": summary_txt
        })
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass

    return jsonify({"message": "Company profile saved", "company_id": profile.id})


@company_bp.get("/profile")
@role_required(UserRole.COMPANY)
def get_company_profile():
    user_id = int(get_jwt_identity())
    profile = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Profile not found", 404, "not_found")

    return jsonify(
        {
            "id": profile.id,
            "company_name": profile.company_name,
            "description": profile.description,
            "website_url": profile.website_url,
            "created_at": profile.created_at.isoformat(),
        }
    )


@company_bp.post("/jobs")
@role_required(UserRole.COMPANY)
def create_job_post():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    min_gpa = parse_optional_gpa(data.get("min_gpa"))
    skills = parse_skill_list(data.get("skills", []))

    profile = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Create company profile first", 400, "missing_profile")
    if not title or not description:
        raise APIError("title and description required", 422, "validation_error")

    job = JobPost(
        company_id=profile.id,
        title=title,
        description=description,
        min_gpa=min_gpa,
        approved=False,
    )
    db.session.add(job)
    db.session.flush()

    _set_job_skills(job, skills)

    db.session.commit()

    try:
        user_obj = User.query.get(user_id)
        uname = f"{profile.company_name} ({user_obj.email})" if user_obj else profile.company_name
        sk_str = ", ".join(skills) if skills else "python, sql, git"
        summary_txt = f"{uname} posted job opening: '{title}' - Skills: {sk_str} [Pending Review]"[:280]
        db.session.execute(text("""
            UPDATE job_post SET username = :uname WHERE id = :jid;
        """), {"uname": uname, "jid": job.id})
        db.session.execute(text("""
            INSERT INTO post_job_opening (
                company_id, username, title, description, min_gpa, approved, skills_required, summary, created_at
            )
            VALUES (:cid, :uname, :title, :desc, :gpa, FALSE, :skills, :summary, CURRENT_TIMESTAMP);
        """), {
            "cid": profile.id,
            "uname": uname,
            "title": title,
            "desc": description,
            "gpa": min_gpa,
            "skills": sk_str,
            "summary": summary_txt
        })
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass

    return jsonify({"message": "Job created, pending admin approval", "job_id": job.id}), 201


@company_bp.get("/jobs")
@role_required(UserRole.COMPANY)
def list_company_jobs():
    user_id = int(get_jwt_identity())
    page, per_page = parse_pagination_args(request)
    approved = request.args.get("approved")

    profile = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({
            "items": [],
            "pagination": {
                "page": 1,
                "per_page": per_page,
                "pages": 0,
                "total": 0,
            }
        })

    query = JobPost.query.filter_by(company_id=profile.id).order_by(JobPost.created_at.desc())

    if approved in {"true", "false"}:
        query = query.filter_by(approved=(approved == "true"))

    payload = serialize_paginated(
        query,
        lambda j: {
            "id": j.id,
            "title": j.title,
            "description": j.description,
            "min_gpa": j.min_gpa,
            "approved": j.approved,
            "skills": [s.name for s in j.skills],
            "applications": len(j.applications),
            "created_at": j.created_at.isoformat(),
        },
        page,
        per_page,
    )
    return jsonify(payload)


@company_bp.get("/applicants/<int:job_id>")
@role_required(UserRole.COMPANY)
def view_applicants(job_id: int):
    user_id = int(get_jwt_identity())
    profile = CompanyProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Company profile not found", 404, "not_found")

    job = JobPost.query.filter_by(id=job_id, company_id=profile.id).first()
    if not job:
        raise APIError("Job not found", 404, "not_found")

    ranked = sorted(job.applications, key=lambda a: a.matching_score, reverse=True)
    return jsonify(
        [
            {
                "application_id": app.id,
                "student_name": app.student.full_name,
                "student_gpa": app.student.gpa,
                "skills": [s.name for s in app.student.skills],
                "matching_score": app.matching_score,
                "status": app.status,
            }
            for app in ranked
        ]
    )
