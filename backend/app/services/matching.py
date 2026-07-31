import os
from functools import lru_cache

from flask import current_app, has_app_context
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.ml_matching import build_feature_map, clamp_score, load_model_bundle, predict_probability_score


def _normalize_skills(skills: list[str]) -> list[str]:
    return sorted({str(skill).strip().lower() for skill in (skills or []) if str(skill).strip()})


def similarity_score(student_skills: list[str], job_skills: list[str]) -> float:
    normalized_student_skills = _normalize_skills(student_skills)
    normalized_job_skills = _normalize_skills(job_skills)

    if not normalized_student_skills or not normalized_job_skills:
        return 0.0

    student_doc = " ".join(normalized_student_skills)
    job_doc = " ".join(normalized_job_skills)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([student_doc, job_doc])
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return round(float(score) * 100, 2)


def _heuristic_matching_score(
    student_skills: list[str],
    job_skills: list[str],
    student_gpa,
    min_gpa,
    priority_skills: list[str] | None = None,
) -> float:
    normalized_job_skills = set(_normalize_skills(job_skills))
    normalized_priority_skills = set(_normalize_skills(priority_skills or []))

    skill_score = similarity_score(student_skills, job_skills)

    if min_gpa is None:
        gpa_score = 100
    elif student_gpa is None:
        gpa_score = 0
    else:
        ratio = min(student_gpa / min_gpa, 1.2)
        gpa_score = round((ratio / 1.2) * 100, 2)

    priority_overlap = len(normalized_priority_skills.intersection(normalized_job_skills))
    priority_score = 0.0
    if normalized_priority_skills:
        # Resume-derived priority skills get stronger influence in the overall score.
        priority_score = round((priority_overlap / len(normalized_priority_skills)) * 100.0, 2)

    high_gpa_bonus = 0.0
    if student_gpa is not None and student_gpa >= 8.5:
        # Strongly reward top CGPA (8.5 to 10.0) with an additional score boost.
        normalized_high_gpa = min(max((student_gpa - 8.5) / 1.5, 0.0), 1.0)
        high_gpa_bonus = round(10.0 + (8.0 * normalized_high_gpa), 2)

    # Give resume-priority skills a strong share so resume upload visibly changes ranking.
    total = (0.5 * skill_score) + (0.2 * gpa_score) + (0.3 * priority_score) + high_gpa_bonus
    return clamp_score(total)


def _resolve_model_path() -> str:
    if has_app_context():
        return current_app.config.get("MATCHING_MODEL_PATH")
    default_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml_artifacts", "matching_model.joblib"))
    return os.getenv("MATCHING_MODEL_PATH", default_path)


@lru_cache(maxsize=1)
def _get_model_bundle():
    model_path = _resolve_model_path()
    try:
        return load_model_bundle(model_path)
    except Exception:
        return None


def reload_matching_model() -> None:
    _get_model_bundle.cache_clear()


def final_matching_score(
    student_skills: list[str],
    job_skills: list[str],
    student_gpa,
    min_gpa,
    priority_skills: list[str] | None = None,
):
    heuristic_score = _heuristic_matching_score(
        student_skills,
        job_skills,
        student_gpa,
        min_gpa,
        priority_skills=priority_skills,
    )

    model_bundle = _get_model_bundle()
    if not model_bundle:
        return heuristic_score

    try:
        features = build_feature_map(
            skill_similarity=similarity_score(student_skills, job_skills),
            student_skills=student_skills,
            job_skills=job_skills,
            student_gpa=student_gpa,
            min_gpa=min_gpa,
            priority_skills=priority_skills,
        )
        model_score = predict_probability_score(model_bundle, features)
        blended_score = (0.75 * model_score) + (0.25 * heuristic_score)
        return clamp_score(blended_score)
    except Exception:
        return heuristic_score


def auto_shortlist(score: float, threshold: float = 60.0) -> bool:
    return score >= threshold
