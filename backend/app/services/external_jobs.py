import re
from typing import Any
from urllib.parse import urlparse

import requests


REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"


COMPANY_DOMAINS: dict[str, str] = {
    "tata consultancy services": "tcs.com",
    "infosys": "infosys.com",
    "wipro": "wipro.com",
    "accenture": "accenture.com",
    "capgemini": "capgemini.com",
    "zoho": "zoho.com",
    "freshworks": "freshworks.com",
    "cognizant": "cognizant.com",
    "hcltech": "hcltech.com",
    "hcl": "hcltech.com",
    "ibm": "ibm.com",
    "oracle": "oracle.com",
    "sap": "sap.com",
}


SEED_JOBS: list[dict[str, Any]] = [
    {
        "company_name": "Tata Consultancy Services",
        "job_title": "Software Engineer",
        "company_description": "Global IT services and consulting company",
        "required_skills": ["python", "java", "sql", "git", "react"],
        "min_gpa": 6.5,
        "apply_url": "https://www.tcs.com/careers",
    },
    {
        "company_name": "Infosys",
        "job_title": "Associate Developer",
        "company_description": "Digital services and consulting company",
        "required_skills": ["python", "javascript", "sql", "html", "css"],
        "min_gpa": 6.0,
        "apply_url": "https://www.infosys.com/careers",
    },
    {
        "company_name": "Wipro",
        "job_title": "Project Engineer",
        "company_description": "Technology services and business process company",
        "required_skills": ["java", "python", "sql", "aws", "docker"],
        "min_gpa": 6.0,
        "apply_url": "https://careers.wipro.com",
    },
    {
        "company_name": "Accenture",
        "job_title": "Application Development Analyst",
        "company_description": "Professional services in cloud and digital technologies",
        "required_skills": ["python", "react", "node", "sql", "api"],
        "min_gpa": 6.8,
        "apply_url": "https://www.accenture.com/in-en/careers",
    },
    {
        "company_name": "Capgemini",
        "job_title": "Software Analyst",
        "company_description": "Consulting and technology services company",
        "required_skills": ["java", "spring", "sql", "rest", "git"],
        "min_gpa": 6.8,
        "apply_url": "https://www.capgemini.com/careers",
    },
    {
        "company_name": "Zoho",
        "job_title": "Full Stack Developer",
        "company_description": "Product company building business software",
        "required_skills": ["javascript", "react", "node", "sql", "python"],
        "min_gpa": 7.2,
        "apply_url": "https://www.zoho.com/careers",
    },
    {
        "company_name": "Freshworks",
        "job_title": "Backend Engineer",
        "company_description": "SaaS customer engagement platform",
        "required_skills": ["python", "go", "mysql", "api", "redis"],
        "min_gpa": 7.4,
        "apply_url": "https://www.freshworks.com/company/careers",
    },
    {
        "company_name": "Cognizant",
        "job_title": "Programmer Analyst",
        "company_description": "IT consulting and digital transformation company",
        "required_skills": ["java", "python", "sql", "linux", "git"],
        "min_gpa": 6.2,
        "apply_url": "https://careers.cognizant.com",
    },
    {
        "company_name": "HCLTech",
        "job_title": "Graduate Engineer Trainee",
        "company_description": "Global technology company delivering engineering and R&D services",
        "required_skills": ["java", "sql", "html", "css", "git"],
        "min_gpa": 6.0,
        "apply_url": "https://www.hcltech.com/careers",
    },
    {
        "company_name": "IBM",
        "job_title": "Application Developer",
        "company_description": "Enterprise technology and cloud solutions provider",
        "required_skills": ["java", "python", "docker", "kubernetes", "api"],
        "min_gpa": 7.5,
        "apply_url": "https://www.ibm.com/careers",
    },
    {
        "company_name": "Oracle",
        "job_title": "Software Developer",
        "company_description": "Cloud infrastructure and enterprise software company",
        "required_skills": ["java", "sql", "spring", "docker", "linux"],
        "min_gpa": 8.0,
        "apply_url": "https://www.oracle.com/careers",
    },
    {
        "company_name": "SAP",
        "job_title": "Cloud Developer",
        "company_description": "Enterprise software company focused on cloud ERP",
        "required_skills": ["java", "node", "typescript", "sql", "api"],
        "min_gpa": 8.2,
        "apply_url": "https://jobs.sap.com",
    },
]


def infer_logo_url(company_name: str, apply_url: str | None = None) -> str | None:
    normalized_name = (company_name or "").strip().lower()
    domain = COMPANY_DOMAINS.get(normalized_name)

    if not domain and apply_url:
        try:
            parsed = urlparse(apply_url)
            host = (parsed.netloc or "").lower()
            if host.startswith("www."):
                host = host[4:]
            if host:
                domain = host
        except ValueError:
            domain = None

    if not domain:
        return None
    return f"https://logo.clearbit.com/{domain}"


def _extract_skill_like_tokens(title: str, description: str, tags: list[str]) -> list[str]:
    source = " ".join([title or "", description or "", " ".join(tags or [])]).lower()
    tokens = re.findall(r"[a-z][a-z0-9+\-#\.]{1,30}", source)
    unique = []
    seen = set()
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        unique.append(token)
    return unique


def fetch_remotive_jobs(search_skills: list[str], timeout_seconds: int = 8, limit: int = 24) -> list[dict[str, Any]]:
    query = " ".join(search_skills[:5]).strip()
    params = {"search": query} if query else {}

    try:
        response = requests.get(REMOTIVE_API_URL, params=params, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json() or {}
    except requests.RequestException:
        return []
    except ValueError:
        return []

    jobs = payload.get("jobs") or []
    normalized: list[dict[str, Any]] = []
    for item in jobs[:limit]:
        title = (item.get("title") or "").strip()
        company_name = (item.get("company_name") or "").strip()
        description = (item.get("description") or "").strip()
        tags = [str(tag).strip().lower() for tag in (item.get("tags") or []) if str(tag).strip()]
        if not title or not company_name:
            continue

        normalized.append(
            {
                "source": "external",
                "external_id": item.get("id"),
                "job_title": title,
                "company_name": company_name,
                "company_description": (item.get("candidate_required_location") or "").strip() or "Remote opportunity",
                "job_description": description,
                "required_skills": _extract_skill_like_tokens(title, description, tags),
                "apply_url": item.get("url"),
                "min_gpa": None,
                "logo_url": infer_logo_url(company_name, item.get("url")),
            }
        )

    return normalized


def fetch_seed_jobs(search_skills: list[str], limit: int = 12) -> list[dict[str, Any]]:
    student_skills = {skill.strip().lower() for skill in search_skills if skill and skill.strip()}

    ranked: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(SEED_JOBS):
        required_skills = [skill.strip().lower() for skill in item["required_skills"] if skill.strip()]
        overlap = len(student_skills.intersection(required_skills))
        # Keep deterministic ordering while preferring higher overlap.
        ranked.append((overlap * 10 - index, {**item, "required_skills": required_skills}))

    ranked.sort(key=lambda row: row[0], reverse=True)

    normalized: list[dict[str, Any]] = []
    for index, (_, item) in enumerate(ranked[:limit]):
        normalized.append(
            {
                "source": "seed",
                "external_id": f"seed-{index + 1}",
                "job_title": item["job_title"],
                "company_name": item["company_name"],
                "company_description": item["company_description"],
                "job_description": item["job_title"],
                "required_skills": item["required_skills"],
                "apply_url": item["apply_url"],
                "min_gpa": item.get("min_gpa"),
                "logo_url": infer_logo_url(item["company_name"], item["apply_url"]),
            }
        )

    return normalized