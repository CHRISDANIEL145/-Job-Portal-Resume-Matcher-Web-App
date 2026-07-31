from collections import Counter
from urllib.parse import quote_plus

from app.models import JobPost
from app.services.matching import final_matching_score


COMPANY_CAREER_LINKS = {
    "tata consultancy services": "https://www.tcs.com/careers",
    "infosys": "https://www.infosys.com/careers",
    "wipro": "https://careers.wipro.com",
    "accenture": "https://www.accenture.com/in-en/careers",
    "capgemini": "https://www.capgemini.com/careers",
    "zoho": "https://www.zoho.com/careers",
    "freshworks": "https://www.freshworks.com/company/careers",
    "cognizant": "https://careers.cognizant.com",
    "hcl": "https://www.hcltech.com/careers",
    "hcltech": "https://www.hcltech.com/careers",
    "ibm": "https://www.ibm.com/careers",
    "oracle": "https://www.oracle.com/careers",
    "sap": "https://jobs.sap.com",
}


def _normalize_skills(skills: list[str] | None) -> list[str]:
    return sorted({str(skill).strip().lower() for skill in (skills or []) if str(skill).strip()})


def _detect_career_track(job_title: str, skills: list[str]) -> str:
    title = (job_title or "").lower()
    skill_set = set(skills)

    if {"nlp", "machine learning", "deep learning", "pandas", "numpy", "scikit-learn"}.intersection(skill_set) or any(
        token in title for token in ["data", "ai", "ml", "machine learning"]
    ):
        return "Data & AI Engineer"
    if {"react", "javascript", "typescript", "node", "css", "html"}.intersection(skill_set) or any(
        token in title for token in ["frontend", "ui", "web", "react"]
    ):
        return "Frontend Product Engineer"
    if {"java", "spring", "api", "sql", "docker", "linux"}.intersection(skill_set) or any(
        token in title for token in ["backend", "platform", "enterprise", "software"]
    ):
        return "Backend Systems Engineer"
    if {"aws", "azure", "gcp", "docker", "kubernetes"}.intersection(skill_set) or any(
        token in title for token in ["cloud", "devops", "infrastructure"]
    ):
        return "Cloud & DevOps Engineer"
    return "Full Stack Builder"


def _project_ideas(skill_gaps: list[str], track_name: str) -> list[dict[str, str]]:
    ideas = []
    gap_text = ", ".join(skill_gaps[:4]) if skill_gaps else "portfolio depth"

    if track_name == "Data & AI Engineer":
        ideas.extend([
            {
                "title": "Resume Intelligence Dashboard",
                "description": "Build a dashboard that extracts resume skills and ranks jobs using similarity + recommendation scores.",
            },
            {
                "title": "Hiring Trend Analyzer",
                "description": f"Use job listings to map the most common missing skills: {gap_text}.",
            },
        ])
    elif track_name == "Frontend Product Engineer":
        ideas.extend([
            {
                "title": "Interactive Career Portfolio",
                "description": "Create a polished portfolio with timeline, projects, and recruiter-ready CTA sections.",
            },
            {
                "title": "Job Match Explorer UI",
                "description": f"Build a searchable job board highlighting CGPA fit and missing skills: {gap_text}.",
            },
        ])
    elif track_name == "Backend Systems Engineer":
        ideas.extend([
            {
                "title": "Application Tracking API",
                "description": "Create a secure backend to track applications, shortlist logic, and notifications.",
            },
            {
                "title": "Skill Graph Service",
                "description": f"Design a service that maps job requirements to your current skills and suggests gaps like {gap_text}.",
            },
        ])
    else:
        ideas.extend([
            {
                "title": "Career Launchpad Web App",
                "description": f"Build a full-stack dashboard with roadmap, jobs, and skill-gap intelligence around {gap_text}.",
            },
            {
                "title": "Project-to-Job Matcher",
                "description": "Link portfolio projects to job roles and show why each project matters to recruiters.",
            },
        ])

    ideas.append(
        {
            "title": "Interview Story Bank",
            "description": "Collect STAR-format stories for your top projects and convert them into interview-ready answers.",
        }
    )
    return ideas[:3]


def _build_preparation_modules(top_jobs: list[dict], skill_gaps: list[str]) -> list[dict]:
    modules = []

    for job in top_jobs[:3]:
        company = job["company_name"]
        role = job["job_title"]
        skills = job.get("required_skills", [])
        missing = job.get("missing_skills", [])
        focus_topics = (skills[:4] or skill_gaps[:4] or ["aptitude", "logic", "projects", "communication"])
        company_key = (company or "").strip().lower()
        company_link = COMPANY_CAREER_LINKS.get(company_key)
        if not company_link:
            company_link = f"https://www.google.com/search?q={quote_plus(company + ' careers') if company else 'company careers'}"

        modules.append(
            {
                "company_name": company,
                "role": role,
                "company_link": company_link,
                "prep_classes": [
                    f"Company context: {company} hiring style and role fit",
                    f"Core stack: {', '.join(focus_topics)}",
                    f"Gap fix: {', '.join(missing[:3]) or 'strengthen portfolio and DS/Algo'}",
                ],
                "quiz": [
                    {
                        "question": f"Why is {role} at {company} a good fit for your profile?",
                        "hint": f"Mention {', '.join(focus_topics[:2]) or 'your strongest skills'} and one project outcome.",
                    },
                    {
                        "question": f"Which skill gap matters most before applying to {company}?",
                        "hint": f"Choose from {', '.join(missing[:3]) or 'your weakest area'} and explain how you will close it.",
                    },
                    {
                        "question": f"What project would you build to impress {company}?",
                        "hint": "Show a product, metrics, and clear technical depth.",
                    },
                ],
                "round_question_bank": [
                    {
                        "round": "Aptitude Round",
                        "questions": [
                            {
                                "question": f"In a 60-minute test at {company}, you attempt 40 questions with +1 and -0.25 marking. If 28 are correct, what is your score?",
                                "focus": "Quant + decision speed",
                                "hint": "Score = correct - 0.25 * incorrect",
                            },
                            {
                                "question": "A train 240m long crosses a 360m platform in 30s. What is the train speed in km/h?",
                                "focus": "Time-speed-distance",
                                "hint": "Total distance / time, then convert m/s to km/h",
                            },
                        ],
                    },
                    {
                        "round": "Coding Round",
                        "questions": [
                            {
                                "question": f"Design an algorithm to find the first non-repeating character in a string stream. Explain complexity and why it suits {role}.",
                                "focus": "Hashing + streaming",
                                "hint": "Think count map + queue",
                            },
                            {
                                "question": f"Given an array of job scores, return top-k candidates efficiently. Which data structure would you use and why?",
                                "focus": "Heap / partial sort",
                                "hint": "Compare O(n log k) vs O(n log n)",
                            },
                        ],
                    },
                    {
                        "round": "Technical Interview",
                        "questions": [
                            {
                                "question": f"How would you design a scalable service for student-job matching with profile updates and re-ranking?",
                                "focus": "System design fundamentals",
                                "hint": "Discuss API, storage, async recompute, and caching",
                            },
                            {
                                "question": f"Pick one of these topics and go deep: {', '.join(focus_topics[:3])}.",
                                "focus": "Core skill depth",
                                "hint": "Use architecture, trade-offs, and debugging examples",
                            },
                        ],
                    },
                    {
                        "round": "HR / Managerial Round",
                        "questions": [
                            {
                                "question": f"Why {company}, and how does your past work map to this role in the first 90 days?",
                                "focus": "Company fit + clarity",
                                "hint": "Use a 30-60-90 day structure",
                            },
                            {
                                "question": "Tell me about a project failure and how you recovered with measurable results.",
                                "focus": "Ownership + resilience",
                                "hint": "Use STAR format with metrics",
                            },
                        ],
                    },
                ],
                "talking_points": [
                    f"Build a one-line pitch for {role}.",
                    "Prepare one project demo and one failure story.",
                    "Practice explaining trade-offs in simple language.",
                ],
            }
        )

    return modules


def build_placement_prep(student_skills: list[str], student_gpa) -> dict:
    normalized_student_skills = _normalize_skills(student_skills)
    launchpad = build_career_launchpad(normalized_student_skills, student_gpa, limit=4)
    top_jobs = launchpad.get("top_jobs", [])
    skill_gaps = launchpad.get("skill_gaps", [])
    company_modules = launchpad.get("prep_modules", [])

    target_company = top_jobs[0]["company_name"] if top_jobs else "Top Recruiters"
    target_role = top_jobs[0]["job_title"] if top_jobs else "Software Engineer"
    focus_topics = (top_jobs[0].get("required_skills", [])[:5] if top_jobs else []) or skill_gaps[:5] or [
        "aptitude",
        "data structures",
        "communication",
    ]

    adaptive_quiz = [
        {
            "type": "aptitude",
            "question": f"You scored 72 in practice and target {target_company}. What should be your first fix?",
            "options": [
                "Increase question volume only",
                "Analyze wrong-answer patterns and patch weak topics",
                "Focus only on HR round",
                "Skip revision and attempt mocks",
            ],
            "answer": "Analyze wrong-answer patterns and patch weak topics",
            "explanation": "Improvement comes from closing weak areas with feedback loops, not just adding volume.",
        },
        {
            "type": "technical",
            "question": f"Which skill is most likely to improve your fit for {target_role}?",
            "options": focus_topics[:4] if len(focus_topics) >= 4 else (focus_topics + ["system design", "sql", "api", "debugging"])[:4],
            "answer": focus_topics[0],
            "explanation": "Start with the highest-frequency role requirement first, then layer advanced topics.",
        },
        {
            "type": "hr",
            "question": "What is the strongest way to answer 'Tell me about yourself' in placements?",
            "options": [
                "List your marks only",
                "Read your resume line by line",
                "Give a 60-second story: skills, proof project, and role fit",
                "Talk about company history only",
            ],
            "answer": "Give a 60-second story: skills, proof project, and role fit",
            "explanation": "Recruiters want concise relevance and evidence, not biography.",
        },
    ]

    mock_rounds = [
        {
            "round": "Round 1 - Aptitude Sprint",
            "duration_minutes": 25,
            "goal": "Accuracy over speed. Target 85%+.",
            "checklist": [
                "Quant shortcuts",
                "Logical elimination",
                "Time box each section",
            ],
        },
        {
            "round": "Round 2 - Coding Core",
            "duration_minutes": 45,
            "goal": "Solve 2 medium problems with clean explanation.",
            "checklist": [
                "One arrays/strings problem",
                "One hashing/two-pointer problem",
                "Explain complexity aloud",
            ],
        },
        {
            "round": "Round 3 - HR + Project Defense",
            "duration_minutes": 20,
            "goal": "Pitch your profile for the target company and role.",
            "checklist": [
                "60-second intro",
                "One deep project walkthrough",
                "Why this company + role",
            ],
        },
    ]

    return {
        "target_company": target_company,
        "target_role": target_role,
        "priority_topics": focus_topics,
        "skill_gaps": skill_gaps,
        "company_modules": company_modules,
        "adaptive_quiz": adaptive_quiz,
        "mock_rounds": mock_rounds,
        "daily_focus": [
            "30 min aptitude",
            "60 min coding",
            "20 min interview answers",
            "10 min revision log",
        ],
    }


def build_career_launchpad(student_skills: list[str], student_gpa, limit: int = 3) -> dict:
    normalized_student_skills = _normalize_skills(student_skills)
    jobs = JobPost.query.filter_by(approved=True).order_by(JobPost.created_at.desc()).all()

    ranked_jobs = []
    gap_counter: Counter[str] = Counter()

    for job in jobs:
        job_skills = [skill.name for skill in job.skills]
        score = final_matching_score(normalized_student_skills, job_skills, student_gpa, job.min_gpa)
        missing_skills = sorted(set(job_skills) - set(normalized_student_skills))
        for skill in missing_skills:
            gap_counter[skill] += 1

        ranked_jobs.append(
            {
                "job_id": job.id,
                "job_title": job.title,
                "company_name": job.company.company_name,
                "company_id": job.company.id,
                "min_gpa": job.min_gpa,
                "matching_score": score,
                "required_skills": job_skills,
                "missing_skills": missing_skills,
                "gpa_eligible": True if student_gpa is None or job.min_gpa is None else float(student_gpa) + 0.15 >= float(job.min_gpa),
                "apply_url": None,
            }
        )

    ranked_jobs.sort(key=lambda item: item["matching_score"], reverse=True)
    top_jobs = ranked_jobs[: max(1, min(limit, 5))]
    target_job = top_jobs[0] if top_jobs else None

    skill_gaps = [skill for skill, _count in gap_counter.most_common(6)]
    track_name = _detect_career_track(target_job["job_title"] if target_job else "", skill_gaps or normalized_student_skills)

    readiness_score = 0
    if top_jobs:
        readiness_score = round(sum(job["matching_score"] for job in top_jobs) / len(top_jobs), 2)

    weekly_plan = [
        {
            "week": "Week 1",
            "theme": "Gap Closing",
            "actions": [
                f"Revise {', '.join(skill_gaps[:3]) or 'core skills'} on your profile and resume.",
                "Add one measurable project bullet for each skill you already have.",
            ],
        },
        {
            "week": "Week 2",
            "theme": "Proof of Work",
            "actions": [
                f"Build a project around {track_name.lower()} that demonstrates your strongest stack.",
                "Publish screenshots or a GitHub README with architecture and results.",
            ],
        },
        {
            "week": "Week 3",
            "theme": "Application Sprint",
            "actions": [
                "Apply to the top matching jobs from the dashboard.",
                "Prepare 3 interview stories from your best project and resume moments.",
            ],
        },
    ]

    return {
        "career_track": track_name,
        "readiness_score": readiness_score,
        "top_strengths": normalized_student_skills[:6],
        "skill_gaps": skill_gaps,
        "top_jobs": top_jobs,
        "project_ideas": _project_ideas(skill_gaps, track_name),
        "prep_modules": _build_preparation_modules(top_jobs, skill_gaps),
        "weekly_plan": weekly_plan,
        "launch_note": f"Your profile is closest to {track_name}. Focus on {', '.join(skill_gaps[:3]) or 'portfolio depth'} to move faster.",
    }