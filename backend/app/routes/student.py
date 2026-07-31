import os
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import CompanyProfile, JobPost, Skill, StudentProfile, UserRole
from app.services.external_jobs import fetch_remotive_jobs, fetch_seed_jobs, infer_logo_url
from app.services.matching import final_matching_score
from app.services.student_intelligence import build_student_intelligence_dashboard, mentor_reply
from app.services.resume_parser import ResumeParser
from app.utils.api import APIError
from app.utils.decorators import role_required
from app.utils.validators import parse_optional_gpa, parse_skill_list
from app.services.ai_features import (
    generate_career_roadmap,
    get_live_skill_trends,
    review_project,
    start_mock_interview,
    submit_interview_answer,
    generate_placement_booster,
    calculate_ats_and_placement_probability
)

student_bp = Blueprint("student", __name__)


def _sync_skills(profile: StudentProfile, skills: list[str]):
    profile.skills = []
    for skill_name in skills:
        skill = Skill.query.filter_by(name=skill_name.lower()).first()
        if not skill:
            skill = Skill(name=skill_name.lower())
            db.session.add(skill)
            db.session.flush()
        profile.skills.append(skill)


def _normalize_skill_set(skills: list[str] | None) -> list[str]:
    return sorted({str(skill).strip().lower() for skill in (skills or []) if str(skill).strip()})


def _score_cutoff(student_skills: list[str], student_gpa) -> float:
    skill_count = len(student_skills)
    if skill_count == 0:
        return 35.0 if student_gpa is None else 28.0
    if skill_count <= 2:
        return 36.0
    if skill_count <= 5:
        return 44.0
    return 50.0


def _is_gpa_eligible(student_gpa, min_gpa) -> bool:
    if min_gpa is None or student_gpa is None:
        return True
    return float(student_gpa) + 0.15 >= float(min_gpa)


def _resume_priority_skills_from_profile(profile: StudentProfile) -> list[str]:
    if not profile.resume_path:
        return []

    resume_path = os.path.join(current_app.config["UPLOAD_FOLDER"], profile.resume_path)
    if not os.path.exists(resume_path):
        return []

    try:
        text = ResumeParser.extract_text(resume_path)
    except Exception:
        return []
    return ResumeParser.extract_skills(text)


def _build_company_recommendations(
    student_skills: list[str],
    student_gpa,
    limit: int = 10,
    priority_skills: list[str] | None = None,
):
    normalized_student_skills = _normalize_skill_set(student_skills)
    normalized_priority_skills = _normalize_skill_set(priority_skills)

    jobs = JobPost.query.filter_by(approved=True).order_by(JobPost.created_at.desc()).all()
    ranked_jobs = []

    for job in jobs:
        job_skills = [skill.name for skill in job.skills]
        gpa_eligible = _is_gpa_eligible(student_gpa, job.min_gpa)
        score = final_matching_score(
            normalized_student_skills,
            job_skills,
            student_gpa,
            job.min_gpa,
            priority_skills=normalized_priority_skills,
        )
        missing_skills = sorted(set(job_skills) - set(normalized_student_skills))

        ranked_jobs.append(
            {
                "source": "local",
                "job_id": job.id,
                "job_title": job.title,
                "company_id": job.company.id,
                "company_name": job.company.company_name,
                "company_description": job.company.description,
                "min_gpa": job.min_gpa,
                "required_skills": job_skills,
                "missing_skills": missing_skills,
                "matching_score": score,
                "gpa_eligible": gpa_eligible,
                "apply_url": job.company.website_url if job.company.website_url else None,
                "logo_url": infer_logo_url(job.company.company_name),
            }
        )

    external_jobs = fetch_remotive_jobs(student_skills, limit=max(limit * 5, 12))
    if len(external_jobs) < limit:
        external_jobs.extend(fetch_seed_jobs(student_skills, limit=max(limit * 2, 8)))

    seen_external = set()
    for ext_job in external_jobs:
        dedupe_key = f"{ext_job.get('company_name', '').lower()}::{ext_job.get('job_title', '').lower()}"
        if dedupe_key in seen_external:
            continue
        seen_external.add(dedupe_key)

        ext_skills = ext_job["required_skills"]
        gpa_eligible = _is_gpa_eligible(student_gpa, ext_job.get("min_gpa"))
        score = final_matching_score(
            normalized_student_skills,
            ext_skills,
            student_gpa,
            ext_job.get("min_gpa"),
            priority_skills=normalized_priority_skills,
        )
        missing_skills = sorted(set(ext_skills) - set(normalized_student_skills))[:15]
        ranked_jobs.append(
            {
                "source": "external",
                "job_id": ext_job["external_id"],
                "job_title": ext_job["job_title"],
                "company_id": f"external-{ext_job['company_name'].lower()}",
                "company_name": ext_job["company_name"],
                "company_description": ext_job["company_description"],
                "min_gpa": None,
                "required_skills": ext_skills[:20],
                "missing_skills": missing_skills,
                "matching_score": score,
                "gpa_eligible": gpa_eligible,
                "apply_url": ext_job.get("apply_url"),
                "logo_url": ext_job.get("logo_url") or infer_logo_url(ext_job["company_name"], ext_job.get("apply_url")),
            }
        )

    ranked_jobs.sort(key=lambda item: (item["gpa_eligible"], item["matching_score"]), reverse=True)

    if student_gpa is not None:
        eligible_jobs = [item for item in ranked_jobs if item["gpa_eligible"]]
        if eligible_jobs:
            ranked_jobs = eligible_jobs

    score_cutoff = _score_cutoff(normalized_student_skills, student_gpa)
    filtered_jobs = [job for job in ranked_jobs if job["matching_score"] >= score_cutoff]
    used_fallback = False
    if not filtered_jobs:
        fallback_count = min(max(3, limit // 2), len(ranked_jobs))
        filtered_jobs = ranked_jobs[:fallback_count]
        used_fallback = True

    top_jobs = filtered_jobs[:limit]
    company_map = {}
    for item in top_jobs:
        company = company_map.get(item["company_id"])
        if not company:
            company_map[item["company_id"]] = {
                "company_id": item["company_id"],
                "company_name": item["company_name"],
                "company_description": item["company_description"],
                "best_match_score": item["matching_score"],
                "logo_url": item.get("logo_url"),
                "top_job": {
                    "job_id": item["job_id"],
                    "job_title": item["job_title"],
                    "min_gpa": item["min_gpa"],
                    "required_skills": item["required_skills"],
                    "missing_skills": item["missing_skills"],
                    "matching_score": item["matching_score"],
                    "gpa_eligible": item["gpa_eligible"],
                    "source": item["source"],
                    "apply_url": item.get("apply_url"),
                },
            }

    companies = sorted(company_map.values(), key=lambda item: item["best_match_score"], reverse=True)

    if not companies:
        fallback_companies = CompanyProfile.query.order_by(CompanyProfile.created_at.desc()).limit(limit).all()
        companies = [
            {
                "company_id": company.id,
                "company_name": company.company_name,
                "company_description": company.description,
                "best_match_score": 0.0,
                "logo_url": infer_logo_url(company.company_name),
                "top_job": None,
            }
            for company in fallback_companies
        ]

    return {
        "recommended_jobs": top_jobs,
        "recommended_companies": companies,
        "meta": {
            "score_cutoff": score_cutoff,
            "used_priority_skills": normalized_priority_skills,
            "used_fallback": used_fallback,
        },
    }


def _build_company_recommendations_from_profile(profile: StudentProfile, limit: int = 10):
    return _build_company_recommendations(
        [skill.name for skill in profile.skills],
        profile.gpa,
        limit=limit,
        priority_skills=_resume_priority_skills_from_profile(profile),
    )


@student_bp.post("/profile")
@role_required(UserRole.STUDENT)
def upsert_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    full_name = (data.get("full_name") or "").strip()
    gpa = parse_optional_gpa(data.get("gpa"))
    skills = parse_skill_list(data.get("skills", []))
    education = (data.get("education") or "").strip() or None

    if not full_name:
        raise APIError("full_name is required", 422, "validation_error")

    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = StudentProfile(user_id=user_id, full_name=full_name)
        db.session.add(profile)

    profile.full_name = full_name
    profile.gpa = gpa
    profile.education = education
    _sync_skills(profile, skills)

    db.session.commit()
    return jsonify(
        {
            "message": "Student profile saved",
            "profile_id": profile.id,
            "recommendations": _build_company_recommendations_from_profile(profile),
        }
    )


@student_bp.post("/resume")
@role_required(UserRole.STUDENT)
def upload_resume():
    user_id = int(get_jwt_identity())
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Create profile first", 400, "missing_profile")

    if "resume" not in request.files:
        raise APIError("No file uploaded", 400, "validation_error")

    file = request.files["resume"]
    if not file.filename.lower().endswith(".pdf"):
        raise APIError("Only PDF allowed", 422, "validation_error")

    filename = secure_filename(f"student_{user_id}_{file.filename}")
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    text = ResumeParser.extract_text(path)
    parsed_skills = ResumeParser.extract_skills(text)
    parsed_education = ResumeParser.extract_education(text)
    parsed_gpa = ResumeParser.extract_gpa(text)

    profile.resume_path = filename
    if parsed_education and profile.education is None:
        profile.education = parsed_education
    if parsed_gpa is not None:
        profile.gpa = parsed_gpa
    existing_skills = [skill.name for skill in profile.skills]
    merged_skills = _normalize_skill_set(existing_skills + parsed_skills)
    if merged_skills:
        _sync_skills(profile, merged_skills)

    db.session.commit()
    recommendations = _build_company_recommendations(
        [skill.name for skill in profile.skills],
        profile.gpa,
        limit=10,
        priority_skills=parsed_skills,
    )

    return jsonify(
        {
            "message": "Resume uploaded and parsed",
            "extracted_skills": parsed_skills,
            "education": profile.education,
            "gpa": profile.gpa,
            "profile_skills": [skill.name for skill in profile.skills],
            "recommendations": recommendations,
        }
    )


@student_bp.get("/profile")
@role_required(UserRole.STUDENT)
def get_profile():
    user_id = int(get_jwt_identity())
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Profile not found", 404, "not_found")

    return jsonify(
        {
            "id": profile.id,
            "full_name": profile.full_name,
            "gpa": profile.gpa,
            "education": profile.education,
            "resume_path": profile.resume_path,
            "skills": [skill.name for skill in profile.skills],
        }
    )


@student_bp.get("/recommendations")
@role_required(UserRole.STUDENT)
def get_recommendations():
    user_id = int(get_jwt_identity())
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Create profile first", 400, "missing_profile")

    return jsonify(_build_company_recommendations_from_profile(profile))


@student_bp.get("/intelligence")
@role_required(UserRole.STUDENT)
def get_intelligence_dashboard():
    user_id = int(get_jwt_identity())
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Create profile first", 400, "missing_profile")

    return jsonify(build_student_intelligence_dashboard(profile))


@student_bp.post("/mentor")
@role_required(UserRole.STUDENT)
def ask_mentor():
    user_id = int(get_jwt_identity())
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Create profile first", 400, "missing_profile")

    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    if not message:
        raise APIError("message is required", 422, "validation_error")

    return jsonify(mentor_reply(profile, message))


@student_bp.post("/recommendations/preview")
@role_required(UserRole.STUDENT)
def get_recommendations_preview():
    data = request.get_json() or {}
    skills = parse_skill_list(data.get("skills", []))
    gpa = parse_optional_gpa(data.get("gpa"))
    limit = data.get("limit", 10)
    try:
        parsed_limit = int(limit)
    except (TypeError, ValueError):
        raise APIError("limit must be an integer", 422, "validation_error")

    parsed_limit = max(1, min(parsed_limit, 10))
    return jsonify(_build_company_recommendations(skills, gpa, limit=parsed_limit))


@student_bp.route("/roadmap", methods=["GET", "POST"])
@role_required(UserRole.STUDENT)
def get_career_roadmap():
    user_id = int(get_jwt_identity())
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Create profile first", 400, "missing_profile")
    
    selected_domain = None
    if request.method == "POST":
        data = request.get_json() or {}
        selected_domain = data.get("domain")
    else:
        selected_domain = request.args.get("domain")
        
    return jsonify(generate_career_roadmap(profile, selected_domain))


@student_bp.get("/skill-trends")
@role_required(UserRole.STUDENT)
def get_skill_trends():
    user_id = int(get_jwt_identity())
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Create profile first", 400, "missing_profile")
    return jsonify(get_live_skill_trends(profile))


@student_bp.post("/project/review")
@role_required(UserRole.STUDENT)
def review_student_project():
    data = request.get_json() or {}
    title = data.get("title")
    description = data.get("description")
    tech_stack = data.get("tech_stack")
    code_snippet = data.get("code_snippet")
    return jsonify(review_project(title, description, tech_stack, code_snippet))


@student_bp.post("/interview/start")
@role_required(UserRole.STUDENT)
def start_interview():
    user_id = int(get_jwt_identity())
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Create profile first", 400, "missing_profile")
    data = request.get_json() or {}
    role = data.get("role", "Full-Stack Generalist Engineer")
    return jsonify(start_mock_interview(role, profile))


@student_bp.post("/interview/submit")
@role_required(UserRole.STUDENT)
def submit_answer():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    answer = data.get("answer")
    if not session_id or answer is None:
        raise APIError("session_id and answer are required", 422, "validation_error")
    return jsonify(submit_interview_answer(session_id, answer))


@student_bp.post("/placement-booster/tailor")
@role_required(UserRole.STUDENT)
def tailor_application():
    user_id = int(get_jwt_identity())
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Create profile first", 400, "missing_profile")
    data = request.get_json() or {}
    job_id = data.get("job_id")
    job_title = data.get("job_title")
    company_name = data.get("company_name")
    required_skills = data.get("required_skills") or data.get("skills") or []

    if not job_id and not job_title:
         raise APIError("job_id or job fallback details are required", 422, "validation_error")

    return jsonify(generate_placement_booster(
        job_id,
        profile,
        fallback_title=job_title,
        fallback_company=company_name,
        fallback_skills=required_skills
    ))


@student_bp.get("/ats-probability")
@role_required(UserRole.STUDENT)
def get_ats_probability():
    user_id = int(get_jwt_identity())
    profile = StudentProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        raise APIError("Create profile first", 400, "missing_profile")
    return jsonify(calculate_ats_and_placement_probability(profile))
