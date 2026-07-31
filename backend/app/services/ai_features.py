import uuid
import re
from app.models import JobPost, StudentProfile, CompanyProfile

# In-memory store for active interview sessions
# Maps session_id -> { "role": str, "skills": list, "current_index": int, "questions": list, "responses": list }
interview_sessions = {}

# Predefined mock questions based on domain
INTERVIEW_BANKS = {
    "frontend": [
        {
            "question": "Explain the difference between Virtual DOM and Real DOM in React.",
            "keywords": ["virtual dom", "reconciliation", "diffing", "batch", "render", "update"],
            "ideal_concepts": "The Virtual DOM is a lightweight copy of the Real DOM. React uses a diffing algorithm (reconciliation) to compare changes and update only the modified nodes in the Real DOM, which improves performance."
        },
        {
            "question": "What is state management, and how do you handle state propagation in large React apps?",
            "keywords": ["redux", "context", "prop drilling", "store", "actions", "reducers", "zustand"],
            "ideal_concepts": "State management holds app state. Large apps use global stores like Redux, Context API, or Zustand to avoid prop drilling and make state changes predictable through unidirectional data flow."
        },
        {
            "question": "How do you optimize a web page's performance to reduce load time?",
            "keywords": ["lazy loading", "code splitting", "minify", "cdn", "image compression", "caching", "bundle size"],
            "ideal_concepts": "Optimize load times by minifying assets, using image compression, leveraging lazy loading and code splitting, caching static assets, and serving content through a CDN."
        }
    ],
    "backend": [
        {
            "question": "Explain the database normalization process and when you would denormalize.",
            "keywords": ["normal form", "redundancy", "join", "foreign key", "performance", "read", "write"],
            "ideal_concepts": "Normalization organizes data into normal forms (1NF, 2NF, 3NF) to eliminate redundancy and maintain integrity. Denormalization is used in read-heavy applications to optimize query performance by reducing joins."
        },
        {
            "question": "Describe what a RESTful API is and how you handle authentication and rate limiting.",
            "keywords": ["rest", "stateless", "jwt", "token", "oauth", "middleware", "rate limit", "redis"],
            "ideal_concepts": "REST is a stateless architectural style. Authentication is typically handled via JWT or OAuth tokens sent in authorization headers. Rate limiting is managed using middleware and token-bucket algorithms (often backed by Redis)."
        },
        {
            "question": "What is database indexing, and how does it affect read and write performance?",
            "keywords": ["index", "b-tree", "lookup", "speed", "write overhead", "scan", "query planner"],
            "ideal_concepts": "Indexing creates a lookup structure (like a B-Tree) that speeds up search queries (reads) but introduces overhead during insertions/updates (writes) since the index must be updated."
        }
    ],
    "data_science": [
        {
            "question": "Explain the difference between overfitting and underfitting and how to address them.",
            "keywords": ["overfit", "underfit", "bias", "variance", "regularization", "cross validation", "dropout"],
            "ideal_concepts": "Overfitting happens when a model learns noise (low bias, high variance). Underfitting happens when a model is too simple (high bias, low variance). Overfitting is solved with regularization (L1/L2, dropout) or more data. Underfitting is solved with more complex models."
        },
        {
            "question": "What is the difference between Precision and Recall? Provide an example where one is preferred.",
            "keywords": ["precision", "recall", "false positive", "false negative", "confusion matrix", "f1 score"],
            "ideal_concepts": "Precision is TP / (TP + FP) (minimizing false positives). Recall is TP / (TP + FN) (minimizing false negatives). In cancer detection, high recall is preferred to avoid missing cases. In spam filtering, high precision is preferred."
        },
        {
            "question": "Describe the main steps of a data cleaning and feature engineering pipeline.",
            "keywords": ["imputation", "outlier", "scaling", "one-hot", "missing value", "normalization"],
            "ideal_concepts": "Pipelines start by handling missing values (imputation) and outliers, followed by scaling numerical features (min-max, standardization) and encoding categorical variables (one-hot encoding) to prep for training."
        }
    ],
    "general": [
        {
            "question": "Describe a challenging technical project you worked on and how you resolved a major blocker.",
            "keywords": ["blocker", "architecture", "debug", "solution", "star method", "refactor"],
            "ideal_concepts": "Explain the situation, task, actions taken (debugging, researching, refactoring), and results using metrics where possible. Focus on systematic problem-solving."
        },
        {
            "question": "How do you manage code quality and collaboration in a software development team?",
            "keywords": ["git", "code review", "pull request", "ci/cd", "agile", "documentation", "testing"],
            "ideal_concepts": "Collaboration is maintained through Git/GitHub pull requests, code review pipelines, automated tests via CI/CD, writing documentation, and using Agile methods to prioritize sprint goals."
        },
        {
            "question": "Explain how you handle learning a brand-new technology under a tight deadline.",
            "keywords": ["learning path", "documentation", "prototype", "mentor", "scaffold", "mvp"],
            "ideal_concepts": "Start with core documentation and tutorials, construct a quick proof-of-concept/MVP to test assumptions, consult mentors or community forums, and focus on required subsets first."
        }
    ]
}

def determine_primary_domain(skills):
    skills_str = " ".join([s.lower() for s in skills])
    frontend_keywords = {"react", "vue", "angular", "html", "css", "javascript", "typescript", "tailwind", "sass", "bootstrap"}
    backend_keywords = {"python", "flask", "django", "node", "express", "java", "spring", "golang", "c#", "net", "ruby", "sql", "postgresql", "mysql", "mongodb", "redis", "docker"}
    ds_keywords = {"pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras", "machine learning", "data science", "nlp", "ai", "r"}

    fe_count = sum(1 for kw in frontend_keywords if kw in skills_str)
    be_count = sum(1 for kw in backend_keywords if kw in skills_str)
    ds_count = sum(1 for kw in ds_keywords if kw in skills_str)

    if fe_count > be_count and fe_count > ds_count:
        return "frontend"
    elif ds_count > fe_count and ds_count > be_count:
        return "data_science"
    elif be_count > 0 or fe_count > 0:
        return "backend"
    return "general"

def generate_career_roadmap(profile, selected_domain=None):
    skills = [skill.name for skill in profile.skills]
    
    if selected_domain:
        normalized = selected_domain.lower().strip()
        if "frontend" in normalized:
            domain = "frontend"
        elif "backend" in normalized:
            domain = "backend"
        elif "science" in normalized or "learning" in normalized or "data" in normalized or "ds" in normalized:
            domain = "data_science"
        else:
            domain = "general"
    else:
        domain = determine_primary_domain(skills)
    
    # Capitalize domain for display
    domain_display = domain.replace("_", " ").title()
    if domain == "data_science":
        domain_display = "Machine Learning & Data Science Specialist"
    
    # Custom roadmaps based on domain
    roadmaps = {
        "frontend": {
            "title": f"AI Career Roadmap: Frontend Engineer Specialist",
            "description": "A comprehensive path to master modern web applications, caching, performance, and UI systems.",
            "phases": [
                {
                    "name": "Phase 1: Advanced Javascript & UI Styling (Weeks 1-4)",
                    "milestone": "Master ES6+, Async/Await, Webpack/Vite bundlers, and Tailwind CSS layouts.",
                    "actions": ["Rebuild core DOM elements from scratch", "Optimize CSS rendering performance", "Master CSS Grid and Responsive Layouts"],
                    "resources": ["MDN JavaScript Guide", "Tailwind CSS Documentation", "JavaScript Info Guide"]
                },
                {
                    "name": "Phase 2: React Core & State Management (Weeks 5-8)",
                    "milestone": "Build reusable components, master Hooks, and implement global state with Redux Toolkit or Zustand.",
                    "actions": ["Implement custom hooks for API polling", "Create a predictable global store", "Integrate client-side routing"],
                    "resources": ["React Dev Docs (New)", "Redux Toolkit Tutorial", "Kent C. Dodds Blog"]
                },
                {
                    "name": "Phase 3: Web Performance & Security (Weeks 9-12)",
                    "milestone": "Audit site performance, implement bundle analyzer, lazy loading, and secure routes from CSRF.",
                    "actions": ["Achieve Lighthouse score >90 on mobile", "Configure code splitting and lazy imports", "Implement authentication guards"],
                    "resources": ["web.dev/fast", "OWASP Web Security Checklist", "Lighthouse Tools Guide"]
                },
                {
                    "name": "Phase 4: Capstone Portfolio & Job Prep (Weeks 13-16)",
                    "milestone": "Publish a rich web application showcasing performance optimizations, and practice interface design interviews.",
                    "actions": ["Build an online mock testing portal", "Rehearse mock coding rounds", "Optimize GitHub repository Readmes"],
                    "resources": ["GreatFrontEnd Interview Prep", "Frontend Masters System Design", "LeetCode JavaScript Card"]
                }
            ]
        },
        "backend": {
            "title": f"AI Career Roadmap: Backend Systems Architect",
            "description": "Your roadmap focuses on building robust databases, secure API routes, load balancing, caching, and scalable infrastructures.",
            "phases": [
                {
                    "name": "Phase 1: REST API Development & Auth (Weeks 1-4)",
                    "milestone": "Implement secure REST endpoints with Flask/Django or Node.js, JWT, and rate limiters.",
                    "actions": ["Create auth middleware utilizing JWT tokens", "Implement robust validation schemas", "Build standardized error handlers"],
                    "resources": ["REST API Design Best Practices", "Flask-JWT-Extended Guide", "OWASP Auth Checklist"]
                },
                {
                    "name": "Phase 2: Database Systems & Caching (Weeks 5-8)",
                    "milestone": "Write efficient SQL queries, design database schemas, index hot columns, and set up Redis caching.",
                    "actions": ["Eliminate N+1 query problems in migrations", "Create B-Tree indices for primary search queries", "Set up Redis for page and session cache"],
                    "resources": ["High-Performance PostgreSQL", "Redis University Courses", "SQL Join Visualizers"]
                },
                {
                    "name": "Phase 3: Docker & Scalable Architecture (Weeks 9-12)",
                    "milestone": "Containerize backend servers, design background task architectures, and orchestrate systems.",
                    "actions": ["Containerize the backend with multi-stage Dockerfiles", "Deploy Celery or Redis Queue for async tasks", "Build API gateway configuration"],
                    "resources": ["Docker Docs & Best Practices", "Celery Task Queue Guide", "System Design Primer Guide"]
                },
                {
                    "name": "Phase 4: Cloud Deployments & Security (Weeks 13-16)",
                    "milestone": "Deploy securely to AWS/GCP, configure SSL certificates, audit logs, and practice backend design.",
                    "actions": ["Set up CI/CD pipeline with GitHub Actions", "Perform penetration tests using OWASP guides", "Rehearse database design mock rounds"],
                    "resources": ["AWS Cloud Practitioner Guide", "GitHub Actions Documentation", "Designing Data-Intensive Applications"]
                }
            ]
        },
        "data_science": {
            "title": f"AI Career Roadmap: Machine Learning & Analytics Specialist",
            "description": "Focus on data preparation, predictive modelling, machine learning pipelines, fine-tuning, and model monitoring.",
            "phases": [
                {
                    "name": "Phase 1: Core Math & Data Cleaning (Weeks 1-4)",
                    "milestone": "Master linear algebra, probability, data ingestion, handling outliers, and Pandas pipelines.",
                    "actions": ["Clean dirty datasets containing missing columns", "Create standardized pipeline transformers", "Calculate statistical distributions"],
                    "resources": ["Mathematics for Machine Learning", "Pandas Cookbook", "Kaggle Data Cleaning Course"]
                },
                {
                    "name": "Phase 2: Classical Machine Learning (Weeks 5-8)",
                    "milestone": "Train regressors, decision trees, random forests, evaluate models with confusion matrices, and tune parameters.",
                    "actions": ["Train Random Forest Classifiers", "Optimize hyperparameters using GridSearchCV", "Document training loss metrics"],
                    "resources": ["Scikit-Learn User Guide", "StatQuest ML Series", "Feature Engineering for ML Book"]
                },
                {
                    "name": "Phase 3: Deep Learning & Pipelines (Weeks 9-12)",
                    "milestone": "Build neural networks, train image classifiers/NLP models using PyTorch/TensorFlow, and deploy API models.",
                    "actions": ["Build Neural Net layers for classification", "Use pre-trained models via transfer learning", "Expose model endpoints via Flask API"],
                    "resources": ["PyTorch Tutorials", "Deep Learning Book (Goodfellow)", "Hugging Face Course"]
                },
                {
                    "name": "Phase 4: ML Operations (MLOps) & Practice (Weeks 13-16)",
                    "milestone": "Configure model monitoring, track experiments with MLflow, and practice machine learning system design.",
                    "actions": ["Track training runs with MLflow metrics", "Build drift-monitoring scripts", "Practice system design for recommendation engines"],
                    "resources": ["Made With ML Course", "MLOps Guide", "Kaggle ML Practice Cards"]
                }
            ]
        },
        "general": {
            "title": f"AI Career Roadmap: Full-Stack Generalist Engineer",
            "description": "Develop versatility across the entire tech stack, enabling you to build, deploy, and verify features end-to-end.",
            "phases": [
                {
                    "name": "Phase 1: Full-Stack Foundation (Weeks 1-4)",
                    "milestone": "Master HTML, CSS, JavaScript, and database basics.",
                    "actions": ["Create responsive CSS layouts", "Build basic database tables", "Write frontend API interactions"],
                    "resources": ["MDN Web Docs", "W3Schools Web Developer Path", "FreeCodeCamp Responsive Design"]
                },
                {
                    "name": "Phase 2: Framework Integration (Weeks 5-8)",
                    "milestone": "Integrate front-end views (React) with server-side endpoints (Node/Flask).",
                    "actions": ["Build an interactive todo dashboard", "Secure routes utilizing server cookies", "Handle form validations in front/backend"],
                    "resources": ["Full Stack Open Course", "Vite + Express Guides", "SQLite Reference Guides"]
                },
                {
                    "name": "Phase 3: Cloud Testing & Security (Weeks 9-12)",
                    "milestone": "Write unit tests, deploy websites, and configure custom environment setups.",
                    "actions": ["Write unit tests using Pytest or Jest", "Deploy code onto Netlify or Render platforms", "Audit configuration secrets"],
                    "resources": ["Testing Javascript Guides", "Render Cloud Hosting Docs", "Twelve-Factor App Methodology"]
                },
                {
                    "name": "Phase 4: System Refinement (Weeks 13-16)",
                    "milestone": "Review coding architecture, optimize queries, and complete job portfolio cards.",
                    "actions": ["Apply MVC refactoring to backend files", "Measure browser loading speeds", "Refine resume layout formatting"],
                    "resources": ["Clean Code (Robert Martin)", "Cracking the Coding Interview", "Visual CV Layout Guides"]
                }
            ]
        }
    }

    # Retrieve roadmap template
    roadmap = roadmaps.get(domain, roadmaps["general"])
    
    # Identify skills to acquire
    demand_skills = {"react", "python", "javascript", "typescript", "docker", "redis", "postgres", "sql", "aws", "git"}
    current_skills_lower = {s.lower() for s in skills}
    skills_to_acquire = sorted(list(demand_skills - current_skills_lower))
    
    roadmap["target_domain"] = domain_display
    roadmap["skills_to_acquire"] = skills_to_acquire[:4] if skills_to_acquire else ["System Design", "Cloud Native Deployments"]
    return roadmap

def get_live_skill_trends(profile):
    skills = [s.name for s in profile.skills]
    skills_lower = {s.lower() for s in skills}
    
    # Curated skill trend metrics
    TREND_DATA = [
        {"skill": "React", "demand_score": 92, "active_openings": 240, "average_salary": "$115,000", "growth": "rising", "companies": ["Meta", "Airbnb", "Netflix"]},
        {"skill": "Python", "demand_score": 95, "active_openings": 310, "average_salary": "$125,000", "growth": "rising", "companies": ["Google", "Netflix", "Instagram"]},
        {"skill": "TypeScript", "demand_score": 88, "active_openings": 190, "average_salary": "$120,000", "growth": "rising", "companies": ["Slack", "Microsoft", "Airbnb"]},
        {"skill": "Docker", "demand_score": 85, "active_openings": 150, "average_salary": "$130,000", "growth": "stable", "companies": ["AWS", "Heroku", "DigitalOcean"]},
        {"skill": "PostgreSQL", "demand_score": 82, "active_openings": 140, "average_salary": "$118,000", "growth": "stable", "companies": ["Uber", "Spotify", "Instagram"]},
        {"skill": "Machine Learning", "demand_score": 96, "active_openings": 280, "average_salary": "$145,000", "growth": "rising", "companies": ["OpenAI", "Google", "Tesla"]},
        {"skill": "AWS", "demand_score": 90, "active_openings": 210, "average_salary": "$135,000", "growth": "rising", "companies": ["Amazon", "Netflix", "Salesforce"]},
        {"skill": "Node.js", "demand_score": 86, "active_openings": 170, "average_salary": "$116,000", "growth": "stable", "companies": ["PayPal", "LinkedIn", "Walmart"]},
        {"skill": "Redis", "demand_score": 78, "active_openings": 95, "average_salary": "$122,000", "growth": "rising", "companies": ["Twitter", "StackOverflow", "Github"]},
        {"skill": "Go (Golang)", "demand_score": 89, "active_openings": 125, "average_salary": "$138,000", "growth": "rising", "companies": ["Uber", "Docker", "Twitch"]}
    ]
    
    # Personalize trend items (whether the student possesses the skill)
    trends = []
    for item in TREND_DATA:
        copied = item.copy()
        copied["student_has_it"] = item["skill"].lower() in skills_lower
        trends.append(copied)
        
    # Sort trends by demand score
    trends.sort(key=lambda x: x["demand_score"], reverse=True)
    return trends

def review_project(title, description, tech_stack, code_snippet=None):
    # Normalize inputs
    title = (title or "").strip()
    description = (description or "").strip()
    tech_stack_list = [t.strip().lower() for t in (tech_stack or "").split(",") if t.strip()]
    code_snippet = (code_snippet or "").strip()

    # Grading scores starting at base parameters
    code_quality_score = 70
    architecture_score = 65
    security_score = 60

    strengths = []
    weaknesses = []
    suggestions = []

    # Analysis based on tech stack
    tech_set = set(tech_stack_list)
    if "react" in tech_set or "typescript" in tech_set:
        strengths.append("Utilizes modern component framework (React) for structured views.")
        architecture_score += 5
    if "postgresql" in tech_set or "mysql" in tech_set:
        strengths.append("Handles relational persistent models using structured schemas.")
        architecture_score += 5
    if "redis" in tech_set:
        strengths.append("Leverages high-speed caching layers to speed up API reads.")
        code_quality_score += 5
    if "jwt" in tech_set or "oauth" in tech_set:
        strengths.append("Implements token-based session verification protocols.")
        security_score += 15
    else:
        weaknesses.append("Missing token authorization standards (e.g. JWT) in API routing.")
        security_score -= 10
        suggestions.append("Incorporate Flask-JWT-Extended or JSON Web Tokens to secure endpoints.")

    # Analysis based on description and code snippet
    code_and_desc = (description + " " + code_snippet).lower()
    
    # Check for unit tests
    if any(term in code_and_desc for term in ["test", "pytest", "jest", "unittest", "assert"]):
        strengths.append("Contains unit testing checks or validation assertions.")
        code_quality_score += 10
    else:
        weaknesses.append("No testing framework (Pytest/Jest) detected in development specs.")
        code_quality_score -= 5
        suggestions.append("Write unit tests using Pytest (Python) or Jest (React) to prevent runtime crashes.")

    # Check for security issues
    if "env" in code_and_desc or "process.env" in code_and_desc or "os.getenv" in code_and_desc:
        strengths.append("Configured environment parameters to shield sensitive API secrets.")
        security_score += 15
    else:
        weaknesses.append("Secret keys or API keys might be hardcoded in files.")
        security_score -= 15
        suggestions.append("Use a `.env` file with `python-dotenv` or `dotenv` NPM package to hide secret tokens.")

    # SQL Injection check
    if re.search(r"execute\(.*%\s*.*\)", code_snippet) or re.search(r"execute\(.*f['\"].*\{.*\}['\"].*\)", code_snippet):
        weaknesses.append("Risk of SQL Injection: detected raw string formatting inside SQL executions.")
        security_score -= 20
        suggestions.append("Replace raw SQL string variables with parameterized queries or SQLAlchemy ORM filters.")
    elif "db.session" in code_and_desc or "sqlalchemy" in code_and_desc or "select" in code_and_desc:
        strengths.append("Employs database isolation or ORM wrappers for secure transactional queries.")
        security_score += 10

    # MVC check
    if any(term in code_and_desc for term in ["controller", "route", "service", "model", "blueprint"]):
        strengths.append("Follows clean separation patterns separating DB models, routes, and views.")
        architecture_score += 10
    else:
        weaknesses.append("Route files may contain direct database queries, violating separation principles.")
        architecture_score -= 5
        suggestions.append("Refactor database execution logic out of route files and move them into a service layer.")

    # Cap scores between 30 and 100
    code_quality_score = max(30, min(100, code_quality_score))
    architecture_score = max(30, min(100, architecture_score))
    security_score = max(30, min(100, security_score))
    overall_score = round((code_quality_score + architecture_score + security_score) / 3, 1)

    # Predefined code improvement example based on tech stack
    code_fix_before = ""
    code_fix_after = ""
    if "python" in tech_set or "flask" in tech_set:
        code_fix_before = "# INSECURE: vulnerable to SQL Injection\nquery = f\"SELECT * FROM users WHERE email = '{user_input}'\"\ndb.session.execute(query)"
        code_fix_after = "# SECURE: utilizing parameterized queries\nquery = \"SELECT * FROM users WHERE email = :email\"\ndb.session.execute(query, {'email': user_input})\n\n# OR using ORM filters:\nuser = User.query.filter_by(email=user_input).first()"
    else:
        code_fix_before = "// INSECURE: vulnerable to prop-drilling or hardcoded keys\nconst secretKey = 'my-super-secret-key-in-code';\nlocalStorage.setItem('key', secretKey);"
        code_fix_after = "// SECURE: load from environment configs\nconst secretKey = process.env.REACT_APP_SECRET_KEY;\n// Or manage state through unified custom Hooks"

    return {
        "title": title or "Unnamed Project",
        "overall_score": overall_score,
        "metrics": {
            "code_quality": code_quality_score,
            "architecture": architecture_score,
            "security": security_score
        },
        "strengths": strengths or ["Basic details recorded."],
        "weaknesses": weaknesses or ["No major red flags detected."],
        "suggestions": suggestions or ["Keep refining the repository clean-up checklist."],
        "code_recommendation": {
            "before": code_fix_before,
            "after": code_fix_after
        }
    }

def start_mock_interview(role, profile):
    # Determine domain bank
    role_lower = (role or "").lower()
    domain = "general"
    if "front" in role_lower or "react" in role_lower or "web" in role_lower:
        domain = "frontend"
    elif "back" in role_lower or "api" in role_lower or "server" in role_lower or "database" in role_lower:
        domain = "backend"
    elif "data" in role_lower or "machine" in role_lower or "model" in role_lower or "ai" in role_lower:
        domain = "data_science"

    # Get questions from bank
    questions = INTERVIEW_BANKS.get(domain, INTERVIEW_BANKS["general"])
    
    # Create interview session
    session_id = str(uuid.uuid4())
    interview_sessions[session_id] = {
        "role": role,
        "domain": domain,
        "current_index": 0,
        "questions": questions,
        "responses": [],
        "student_name": profile.full_name
    }

    return {
        "session_id": session_id,
        "role": role,
        "domain": domain,
        "current_index": 0,
        "total_questions": len(questions),
        "first_question": questions[0]["question"]
    }

def submit_interview_answer(session_id, answer):
    session = interview_sessions.get(session_id)
    if not session:
        return {"error": "Invalid or expired session"}, 404

    current_idx = session["current_index"]
    questions = session["questions"]
    question_data = questions[current_idx]

    # Evaluate response
    ans_lower = (answer or "").lower().strip()
    words = ans_lower.split()
    word_count = len(words)

    # Baseline calculations
    matched_keywords = []
    for kw in question_data["keywords"]:
        if kw in ans_lower:
            matched_keywords.append(kw)

    # Scoring algorithm
    keyword_score = (len(matched_keywords) / len(question_data["keywords"])) * 60
    length_score = min(40, (word_count / 30) * 40) # Max length score reached at 30 words
    total_score = round(keyword_score + length_score, 1)
    
    # Cap total score between 10 and 100
    total_score = max(10, min(100, total_score))

    # Review comments
    strengths = []
    weaknesses = []
    
    if word_count < 10:
        weaknesses.append("Your response was too brief. Try to elaborate on structural details or explain terms.")
    else:
        strengths.append("Provided a reasonably structured explanation with good descriptive depth.")

    if len(matched_keywords) >= 2:
        strengths.append(f"Successfully integrated technical terminology: {', '.join(matched_keywords[:3])}.")
    else:
        weaknesses.append("Missing core technical vocabulary that is expected for this concept.")
        
    # Construct feedback
    feedback = {
        "score": total_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "model_answer": question_data["ideal_concepts"]
    }

    # Record response
    session["responses"].append({
        "question": question_data["question"],
        "student_answer": answer,
        "score": total_score,
        "feedback": feedback
    })

    # Progress session
    session["current_index"] += 1
    next_idx = session["current_index"]

    if next_idx < len(questions):
        next_question = questions[next_idx]["question"]
        return {
            "completed": False,
            "session_id": session_id,
            "current_index": next_idx,
            "feedback_on_previous": feedback,
            "next_question": next_question
        }
    else:
        # Generate final report
        scores = [res["score"] for res in session["responses"]]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        grade = "Needs Improvement"
        if avg_score >= 85:
            grade = "Excellent (Interview Ready)"
        elif avg_score >= 70:
            grade = "Solid (Competitive)"
        elif avg_score >= 50:
            grade = "Developing (Needs Revision)"

        final_report = {
            "completed": True,
            "session_id": session_id,
            "average_score": avg_score,
            "grade": grade,
            "summary_feedback": f"Completed 3 interview challenges. Final evaluated average is {avg_score}%. " +
                               ("Focus on incorporating more technical keywords and structural flow." if avg_score < 75 else "Great work! You demonstrated solid depth and keyword accuracy."),
            "responses": session["responses"]
        }
        
        # Clean up session
        if session_id in interview_sessions:
            del interview_sessions[session_id]

        return final_report

def generate_placement_booster(job_id, profile, fallback_title=None, fallback_company=None, fallback_skills=None):
    job = None
    try:
        if job_id and not str(job_id).startswith("external"):
            job = JobPost.query.get(int(job_id))
    except (ValueError, TypeError):
        pass

    if job:
        company_name = job.company.company_name
        job_title = job.title
        job_skills = [s.name for s in job.skills]
    else:
        company_name = fallback_company or "Target Company"
        job_title = fallback_title or "Software Developer"
        job_skills = fallback_skills or []

    skills = [s.name for s in profile.skills]
    skills_lower = {s.lower() for s in skills}
    job_skills_lower = {s.lower() for s in job_skills}

    matching = sorted(list(skills_lower & job_skills_lower))
    missing = sorted(list(job_skills_lower - skills_lower))

    # Capitalize for display
    matching_disp = [m.title() for m in matching]
    missing_disp = [m.title() for m in missing]

    student_name = profile.full_name or "Candidate"

    # Build customized Elevator Pitch
    matching_str = ", ".join(matching_disp[:3]) if matching_disp else "my software development foundations"
    pitch = (
        f"Hi, I'm {student_name}. I am a developer specializing in backend and frontend structures. "
        f"I saw the {job_title} opening at {company_name} and was immediately drawn to it. "
        f"With my background in {matching_str}, I am confident I can contribute from day one. "
        f"I noticed the role also involves {missing_disp[0] if missing_disp else 'advanced configurations'}, and I have already begun "
        f"expanding my skills in that direction. I would love to bring my technical drive to the team."
    )

    # Build customized Cover Letter
    cover_letter = (
        f"Dear Hiring Team at {company_name},\n\n"
        f"I am writing to express my strong interest in the {job_title} position at your esteemed company. "
        f"As a developer with hand-on experience in building scalable projects, I align closely with your team's tech stack.\n\n"
        f"My background matches several requirements for this role, specifically in {', '.join(matching_disp) if matching_disp else 'engineering systems'}. "
        f"In my previous projects, I focused on clean design patterns and efficient database lookups, resulting in reliable "
        f"features. "
    )
    if missing_disp:
        cover_letter += (
            f"While I am currently strengthening my skills in {', '.join(missing_disp[:2])}, I learn quickly "
            f"and am already working on building custom project layouts utilizing these technologies. "
        )
    cover_letter += (
        f"\n\nI am eager to contribute my problem-solving skills and project dedication to {company_name}. "
        f"Thank you for your time and consideration.\n\n"
        f"Sincerely,\n"
        f"{student_name}"
    )

    # Build Cold Outreach message
    outreach = (
        f"Hi [Name],\n\n"
        f"I hope you're having a great week! I saw you work at {company_name} and noticed the team is hiring "
        f"a {job_title}. I recently applied and was impressed by the team's work on modern stacks.\n\n"
        f"I have a background in {matching_str} and wanted to reach out to see if you have any advice for "
        f"standing out in the application process. I'd love to connect!\n\n"
        f"Best regards,\n"
        f"{student_name}"
    )

    # Build CV Adjustments
    adjustments = [
        f"Highlight your experience in {matching_disp[0]} at the top of your resume skill list." if matching_disp else "Add a clean project summary section at the top.",
        f"List projects where you utilized {', '.join(matching_disp[:2])} with clear bullet points." if len(matching_disp) >= 2 else "Detail your software design coursework and project timelines.",
        f"Add a 'Learning Path' section highlighting {missing_disp[0]} to show proactive skill building." if missing_disp else "Add a certifications section to show extra-curricular learning."
    ]

    return {
        "job_title": job_title,
        "company_name": company_name,
        "elevator_pitch": pitch,
        "cover_letter": cover_letter,
        "cold_outreach": outreach,
        "cv_adjustments": adjustments
    }

def calculate_ats_and_placement_probability(profile):
    skills = [s.name for s in profile.skills]
    skills_lower = {s.lower() for s in skills}
    
    # 1. ATS Compliance score calculations
    ats_score = 45 # Base score
    ats_feedback = []
    
    if profile.resume_path:
        ats_score += 20
        ats_feedback.append("Resume PDF uploaded successfully (+20)")
    else:
        ats_feedback.append("Missing resume PDF upload (-15)")

    if profile.education:
        ats_score += 15
        ats_feedback.append("Education history documented (+15)")
    else:
        ats_feedback.append("Missing educational benchmarks (-10)")

    if len(skills) >= 8:
        ats_score += 15
        ats_feedback.append("Good technical keyword density (+15)")
    elif len(skills) >= 4:
        ats_score += 10
        ats_feedback.append("Average keyword density (+10)")
    else:
        ats_feedback.append("Thin skill coverage; add 4+ role-aligned terms (-10)")

    if profile.gpa is not None:
        ats_score += 5
        ats_feedback.append("CGPA score reported (+5)")
    else:
        ats_feedback.append("Missing CGPA records (-5)")
        
    ats_score = max(20, min(100, ats_score))

    # Critical optimization recommendations
    ats_suggestions = []
    if not profile.resume_path:
        ats_suggestions.append("Upload a standard PDF resume containing your contact details and active links.")
    if len(skills) < 6:
        ats_suggestions.append("Incorporate trending keywords (e.g. Docker, Python, REST APIs) in your profile skill list.")
    if not profile.education:
        ats_suggestions.append("Fill in your degree name, university details, and graduation year.")
    if len(ats_suggestions) == 0:
        ats_suggestions.append("Your ATS score is solid! Add specific numerical metrics to your project reviews to score higher.")

    # 2. Placement probability match across all active companies
    companies = CompanyProfile.query.all()
    probability_matrix = []
    
    for company in companies:
        # Check active jobs of company
        jobs = JobPost.query.filter_by(company_id=company.id, approved=True).all()
        if not jobs:
            continue
            
        best_probability = 30 # Default probability
        matched_job = None
        
        for job in jobs:
            job_skills = [s.name for s in job.skills]
            job_skills_lower = {s.lower() for s in job_skills}
            
            # Intersection score
            matching = skills_lower & job_skills_lower
            match_pct = (len(matching) / len(job_skills)) if job_skills else 1.0
            
            # Final probability check
            gpa_ok = True
            if profile.gpa is not None and job.min_gpa is not None:
                gpa_ok = float(profile.gpa) + 0.15 >= float(job.min_gpa)
                
            job_prob = 30
            if gpa_ok:
                job_prob += 20
                job_prob += int(match_pct * 40)
            else:
                job_prob -= 15
                
            if profile.resume_path:
                job_prob += 10
                
            job_prob = max(10, min(95, job_prob))
            
            if job_prob > best_probability:
                best_probability = job_prob
                matched_job = job
                
        if not matched_job:
            continue
            
        prob_tier = "Needs Alignment"
        if best_probability >= 75:
            prob_tier = "High"
        elif best_probability >= 50:
            prob_tier = "Medium"
            
        critical_actions = []
        missing_skills = [s.name for s in matched_job.skills if s.name.lower() not in skills_lower]
        if missing_skills:
            critical_actions.append(f"Acquire {missing_skills[0]} to close the tech stack gap.")
        if not profile.resume_path:
            critical_actions.append("Upload resume to pass the auto-shortlist filter.")
        if profile.gpa is not None and matched_job.min_gpa is not None and float(profile.gpa) < float(matched_job.min_gpa):
            critical_actions.append(f"Company requires min CGPA of {matched_job.min_gpa}. Leverage strong project reviews to bypass.")
        if len(critical_actions) == 0:
            critical_actions.append("Ready to apply! Tailor your application booster before submitting.")

        probability_matrix.append({
            "company_name": company.company_name,
            "target_role": matched_job.title,
            "probability": best_probability,
            "tier": prob_tier,
            "critical_actions": critical_actions[:2]
        })
        
    probability_matrix.sort(key=lambda x: x["probability"], reverse=True)

    return {
        "ats_score": ats_score,
        "ats_feedback": ats_feedback,
        "ats_suggestions": ats_suggestions,
        "placement_matrix": probability_matrix
    }
