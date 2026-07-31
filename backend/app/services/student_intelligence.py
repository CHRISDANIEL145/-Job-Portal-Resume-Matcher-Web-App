from collections import Counter

from app.models import JobPost, StudentProfile
from app.services.external_jobs import fetch_seed_jobs


def _normalize_skills(skills: list[str] | None) -> list[str]:
    return sorted({str(skill).strip().lower() for skill in (skills or []) if str(skill).strip()})


def _student_skill_names(profile: StudentProfile) -> list[str]:
    return [skill.name for skill in profile.skills]


def _is_gpa_eligible(student_gpa, min_gpa) -> bool:
    if student_gpa is None or min_gpa is None:
        return True
    return float(student_gpa) + 0.15 >= float(min_gpa)


def build_demand_hiring_analyzer(profile: StudentProfile) -> dict:
    student_skills = set(_normalize_skills(_student_skill_names(profile)))
    student_gpa = profile.gpa
    jobs = JobPost.query.filter_by(approved=True).all()
    gpa_filtered_jobs = [job for job in jobs if _is_gpa_eligible(student_gpa, job.min_gpa)]
    demand_jobs = gpa_filtered_jobs or jobs

    skill_counter: Counter[str] = Counter()
    company_counter: Counter[str] = Counter()
    role_counter: Counter[str] = Counter()

    for job in demand_jobs:
        company_counter[job.company.company_name] += 1
        role_counter[job.title] += 1
        for skill in _normalize_skills([skill.name for skill in job.skills]):
            skill_counter[skill] += 1

    using_seed_fallback = False
    if not jobs:
        using_seed_fallback = True
        seed_jobs = fetch_seed_jobs(list(student_skills), limit=12)
        gpa_filtered_seed_jobs = [
            item for item in seed_jobs if _is_gpa_eligible(student_gpa, item.get("min_gpa"))
        ]
        demand_seed_jobs = gpa_filtered_seed_jobs or seed_jobs
        for seed_job in demand_seed_jobs:
            company_counter[seed_job["company_name"]] += 1
            role_counter[seed_job["job_title"]] += 1
            for skill in _normalize_skills(seed_job.get("required_skills") or []):
                skill_counter[skill] += 1

    top_skills = [
        {"skill": skill, "demand": count, "you_have_it": skill in student_skills}
        for skill, count in skill_counter.most_common(8)
    ]
    missing_skills = [item["skill"] for item in top_skills if not item["you_have_it"]][:5]

    top_companies = [{"company": company, "openings": count} for company, count in company_counter.most_common(5)]
    top_roles = [{"role": role, "openings": count} for role, count in role_counter.most_common(5)]

    if top_skills and using_seed_fallback:
        summary = (
            f"No approved campus jobs are live yet, so this view shows current market demand. "
            f"Top pull is for {top_skills[0]['skill']} and {top_skills[1]['skill'] if len(top_skills) > 1 else top_skills[0]['skill']}."
        )
    elif top_skills:
        summary = f"The market is pulling hardest on {top_skills[0]['skill']} and {top_skills[1]['skill'] if len(top_skills) > 1 else top_skills[0]['skill']}."
    else:
        summary = "No approved jobs are live yet, so demand is still forming."

    return {
        "summary": summary,
        "top_skills": top_skills,
        "top_roles": top_roles,
        "top_companies": top_companies,
        "missing_skills": missing_skills,
        "gpa_context": {
            "student_gpa": student_gpa,
            "eligible_openings": len(demand_jobs),
            "total_openings": len(jobs),
        },
        "action_plan": [f"Strengthen {skill}" for skill in missing_skills[:3]]
        or ["Keep your profile updated and revisit when more jobs go live."],
    }


def build_resume_weakness_detector(profile: StudentProfile) -> dict:
    skill_names = _normalize_skills(_student_skill_names(profile))
    weaknesses = []
    strengths = []

    if profile.resume_path:
        strengths.append("Resume uploaded and available for parsing")
    else:
        weaknesses.append("Resume has not been uploaded yet")

    if profile.education:
        strengths.append("Education section is present")
    else:
        weaknesses.append("Education section is missing")

    if profile.gpa is None:
        weaknesses.append("CGPA is missing")
    elif profile.gpa >= 8.5:
        strengths.append(f"Strong CGPA of {profile.gpa} strengthens your shortlisting profile")
    elif profile.gpa >= 7.0:
        strengths.append(f"CGPA of {profile.gpa} is solid for many entry-level roles")
    else:
        weaknesses.append("CGPA is below the preferred threshold for many roles")

    if len(skill_names) < 3:
        weaknesses.append("Skill coverage is thin; add more role-specific keywords")
    else:
        strengths.append(f"{len(skill_names)} skills captured in profile")

    if len(skill_names) >= 1 and len(skill_names) < 5:
        weaknesses.append("No evidence of project depth in the skill mix")

    if not weaknesses:
        weaknesses.append("No major weaknesses detected from the saved profile")

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "next_steps": [
            "Upload a structured PDF resume with projects and metrics.",
            "Add 3 to 5 job-aligned skills that match live demand.",
            "Include measurable project outcomes in the education or summary section.",
        ],
    }


def mentor_reply(profile: StudentProfile, message: str) -> dict:
    text = (message or "").strip().lower()
    skills = _normalize_skills(_student_skill_names(profile))
    top_skill = skills[0] if skills else "your core stack"
    demand = build_demand_hiring_analyzer(profile)
    missing_skill = demand['missing_skills'][0] if demand['missing_skills'] else "advanced system design"

    kb_rules = {
        "virtual_dom": ["virtual dom", "vdom", "react dom", "diffing", "reconciliation"],
        "props_vs_state": ["state vs props", "props vs state", "prop vs state", "difference between state and props"],
        "rest_api": ["rest api", "restful", "http methods", "post vs get", "get vs post"],
        "jwt_auth": ["jwt", "json web token", "auth token", "stateless auth"],
        "database_normalization": ["normalization", "1nf", "2nf", "3nf", "normal form"],
        "indexing": ["database index", "indexing", "b-tree", "db index"],
        "joins": ["join", "inner join", "left join", "sql join"],
        "deadlock": ["deadlock", "deadlocks", "process sync", "philosophers"],
        "process_vs_thread": ["process vs thread", "thread vs process", "multithreading", "concurrency"],
        "virtual_memory": ["virtual memory", "paging", "page fault", "segmentation"],
        "tcp_vs_udp": ["tcp vs udp", "udp vs tcp", "datagram"],
        "http_vs_https": ["http vs https", "https vs http", "ssl", "tls"],
        "dns": ["dns", "domain name system", "name resolution"],
        "time_complexity": ["time complexity", "space complexity", "big o", "big-o", "complexity"],
        "star_framework": ["star method", "star framework", "behavioral question"],
        "resume_tips": ["resume", "cv", "ats", "resume tips", "improve resume", "resume review", "resume gap"],
        "gpa_tips": ["gpa", "cgpa", "low gpa", "gpa threshold"],
        "skills_gap": ["skill gap", "missing skill", "tech stack", "profile skills"],
        "project_architecture": ["mvc", "microservices", "system design", "monolith", "design patterns"]
    }

    kb = {
        "virtual_dom": {
            "reply": "📌 **Virtual DOM in React**:\n"
                     "The Virtual DOM (VDOM) is a lightweight programming concept where an ideal, or 'virtual', representation of a UI is kept in memory and synced with the 'real' DOM by a library such as ReactDOM. This synchronization process is called **reconciliation**.\n\n"
                     "🛠 *React Code Example*:\n"
                     "```javascript\n"
                     "// React re-renders this Virtual DOM element first before touching the browser layout:\n"
                     "const [value, setValue] = useState(0);\n"
                     "return <button onClick={() => setValue(value + 1)}>{value}</button>;\n"
                     "```\n\n"
                     "💡 *Key Revision Points*:\n"
                     "- Modifying the real browser DOM triggers layout recalculations and repaint operations, which are computationally expensive.\n"
                     "- React runs a heuristic O(n) **diffing algorithm** to compare virtual trees and compute minimal updates.\n"
                     "🎓 *Interview Tip*: Emphasize that the Virtual DOM groups (batches) updates together, preventing layout thrashing.",
            "follow_up": ["Explain React state vs props", "Explain REST APIs", "Detail Database Indexing"]
        },
        "props_vs_state": {
            "reply": "📌 **State vs. Props in React**:\n"
                     "- **Props** (short for properties) are read-only components passed down from parent to child. They allow configurations and data injection.\n"
                     "- **State** is a local data structure managed internally within the component. It represents mutable values that trigger re-rendering when changed.\n\n"
                     "🛠 *React Code Example*:\n"
                     "```javascript\n"
                     "// Props are received; state is managed locally:\n"
                     "function ChildComponent({ title }) { // title is a prop\n"
                     "  const [count, setCount] = useState(0); // count is state\n"
                     "  return <button onClick={() => setCount(count + 1)}>{title}: {count}</button>;\n"
                     "}\n"
                     "```\n\n"
                     "💡 *Key Revision Points*:\n"
                     "- Props are immutable from the child's perspective.\n"
                     "- State updates are asynchronous and batched by React for rendering efficiency.\n"
                     "🎓 *Interview Tip*: Mention that state changes flow down as props to children, maintaining a predictable unidirectional data flow model.",
            "follow_up": ["Explain Virtual DOM", "Explain Redux Toolkit", "Describe STAR Framework"]
        },
        "rest_api": {
            "reply": "📌 **RESTful API Architectural Principles**:\n"
                     "Representational State Transfer (REST) is a stateless, client-server design style using HTTP protocols:\n"
                     "- **GET**: Retrieve resource representation.\n"
                     "- **POST**: Create a new resource.\n"
                     "- **PUT**: Replace a resource or create it if missing.\n"
                     "- **PATCH**: Partially modify an existing resource.\n"
                     "- **DELETE**: Remove a resource.\n\n"
                     "🛠 *REST API Example (Python Flask)*:\n"
                     "```python\n"
                     "@app.route('/jobs/<int:id>', methods=['GET'])\n"
                     "def get_job(id):\n"
                     "    return jsonify({'job_id': id, 'title': 'Software Engineer'})\n"
                     "```\n\n"
                     "💡 *Key Revision Points*:\n"
                     "- Statelessness: Each request from client must contain all context and authentication tokens required to parse it.\n"
                     "- Uniform Interface: Resources are identified by URIs (e.g. `/api/v1/students`).\n"
                     "🎓 *Interview Tip*: If asked about idempotency: GET, PUT, and DELETE are idempotent (multiple identical calls yield same state), while POST is not.",
            "follow_up": ["Explain JWT Authentication", "Difference between PUT and PATCH", "Explain HTTP vs HTTPS"]
        },
        "jwt_auth": {
            "reply": "📌 **JSON Web Token (JWT) Authentication**:\n"
                     "JWT is an open standard (RFC 7519) that defines a compact, URL-safe way to transmit information securely between parties as a JSON object. It consists of three parts separated by dots:\n"
                     "1. **Header**: Specifies token type and signature algorithm (e.g. HS256).\n"
                     "2. **Payload**: Contains claims (user identity, roles, expiration timestamp).\n"
                     "3. **Signature**: Cryptographic checksum created by signing header+payload with a private secret key.\n\n"
                     "🛠 *Structure representation*:\n"
                     "`header.payload.signature` sent in HTTP Header: `Authorization: Bearer <token>`.\n\n"
                     "💡 *Key Revision Points*:\n"
                     "- Stateless: The server does not store active session rows; it validates the signature cryptographically.\n"
                     "- Security: Payloads are base64 encoded and readable by anyone. Do NOT place sensitive secrets (like passwords) in payload.\n"
                     "🎓 *Interview Tip*: Explain how to handle logout in JWT: since tokens are stateless, logouts require client-side token deletion or server-side blacklist caches using Redis.",
            "follow_up": ["Explain REST APIs", "Explain SQL injection audits", "Describe Process vs Thread"]
        },
        "database_normalization": {
            "reply": "📌 **Database Normalization (1NF, 2NF, 3NF)**:\n"
                     "Normalization structures relational database tables to prevent update anomalies and remove redundant data:\n"
                     "- **1NF (First Normal Form)**: Atomic columns (no sets/arrays) and unique primary keys.\n"
                     "- **2NF (Second Normal Form)**: Meet 1NF + remove partial dependencies (non-key columns must depend on the *entire* primary key, not a subset of a composite key).\n"
                     "- **3NF (Third Normal Form)**: Meet 2NF + remove transitive dependencies (non-key columns must not depend on other non-key columns).\n\n"
                     "🛠 *Transitive dependency example*:\n"
                     "If table has `EmployeeID -> DepartmentID` and `DepartmentID -> DepartmentName`, then `DepartmentName` is transitively dependent on `EmployeeID`. 3NF splits this into an `Employees` table and a `Departments` table.\n\n"
                     "💡 *Key Revision Points*:\n"
                     "- Normalization speeds up database writes and prevents data conflicts.\n"
                     "- Denormalization is used in read-heavy architectures (like OLAP) to avoid expensive table joins.\n"
                     "🎓 *Interview Tip*: Know Boyce-Codd Normal Form (BCNF): a stronger version of 3NF where every determinant must be a candidate key.",
            "follow_up": ["Difference between normal forms and denormalization", "Explain Database Indexing", "Explain SQL Joins"]
        },
        "indexing": {
            "reply": "📌 **Database Indexing & B-Trees**:\n"
                     "An index is a database structure that speeds up retrieval of query rows at the cost of slower writes and additional storage. Relational engines typically index columns using balanced search trees (**B-Trees**).\n\n"
                     "🛠 *SQL Index Example*:\n"
                     "```sql\n"
                     "CREATE INDEX idx_student_skills ON StudentProfile(gpa, user_id);\n"
                     "```\n\n"
                     "💡 *Key Revision Points*:\n"
                     "- Read Performance: High-speed O(log N) lookups instead of slow O(N) sequential table scans.\n"
                     "- Write Overhead: Every INSERT, UPDATE, or DELETE requires reorganizing the nodes of the B-Tree.\n"
                     "🎓 *Interview Tip*: Mention the 'Leftmost Prefix Rule' in composite indices: an index on `(colA, colB)` helps queries filtering on `colA` or `(colA, colB)`, but does NOT speed up searches filtering *only* on `colB`.",
            "follow_up": ["Explain Database Normalization", "Explain SQL Joins", "Explain Time Complexity and Big O"]
        },
        "joins": {
            "reply": "📌 **SQL Joins Explained**:\n"
                     "- **INNER JOIN**: Returns rows only when there is a match in both tables.\n"
                     "- **LEFT JOIN (LEFT OUTER)**: Returns all rows from left table, plus matching rows from right. Non-matching right cells yield `NULL`.\n"
                     "- **RIGHT JOIN**: Returns all rows from right table, plus matching rows from left.\n"
                     "- **FULL OUTER JOIN**: Returns all rows when there is a match in either table.\n\n"
                     "🛠 *SQL Join Example*:\n"
                     "```sql\n"
                     "SELECT S.full_name, A.status \n"
                     "FROM StudentProfile S \n"
                     "INNER JOIN Application A ON S.id = A.student_id;\n"
                     "```\n\n"
                     "💡 *Key Revision Points*:\n"
                     "- Make sure columns used inside your `ON` clauses are indexed to avoid slow nested loops.\n"
                     "- Database query planners select between Hash Join, Merge Join, or Nested Loop depending on table size.\n"
                     "🎓 *Interview Tip*: Practice detailing the difference between `WHERE` filters and `ON` join filters: `ON` filters are evaluated during matching, while `WHERE` filters run after the join completes.",
            "follow_up": ["Explain Database Indexing", "Explain REST APIs", "Explain MVC Architecture"]
        },
        "deadlock": {
            "reply": "📌 **Operating System Deadlocks**:\n"
                     "A deadlock occurs when a set of processes are blocked because each process holds a resource and waits for another resource held by another process in the same set.\n\n"
                     "💡 *The Coffman Conditions (Must all hold for deadlock to occur)*:\n"
                     "1. **Mutual Exclusion**: Resources cannot be shared.\n"
                     "2. **Hold and Wait**: Process holding resources can request new ones.\n"
                     "3. **No Preemption**: Resources cannot be forcibly taken from a process.\n"
                     "4. **Circular Wait**: Process A waits for B, B waits for C, C waits for A.\n\n"
                     "🎓 *Interview Tip*: Emphasize **Deadlock Prevention** vs **Detection**. Prevention invalidates one of the Coffman conditions (e.g. resource ordering). Detection allows deadlocks to occur and resolves them via rollbacks.",
            "follow_up": ["Explain Process vs Thread", "Explain Virtual Memory & Page Faults", "Explain TCP vs UDP"]
        },
        "process_vs_thread": {
            "reply": "📌 **Process vs. Thread (Operating Systems)**:\n"
                     "- **Process**: An executing instance of a program. It has its own independent address space, memory map, file descriptors, and security context. Processes are isolated from one another.\n"
                     "- **Thread**: The smallest unit of execution inside a process. Threads share the parent process's memory space (code, heap, global variables) but have their own individual stack and program counter.\n\n"
                     "💡 *Key Revision Points*:\n"
                     "- Communication: Processes communicate via IPC (sockets, pipes, shared memory). Threads communicate directly since they share memory.\n"
                     "- Creation Cost: Spawning a process is slow and resource-heavy (context switching cost is high). Spawning a thread is fast and lightweight.\n"
                     "🎓 *Interview Tip*: Be ready to discuss the **Global Interpreter Lock (GIL)** if asked about multithreading in Python: Python threads do not run in true parallel on multi-core machines because the GIL restricts execution to one thread at a time.",
            "follow_up": ["Explain OS Deadlocks", "Explain Virtual Memory & Page Faults", "Describe DNS"]
        },
        "virtual_memory": {
            "reply": "📌 **Virtual Memory, Paging & Page Faults**:\n"
                     "Virtual memory mapping decouples a program's logical address space from physical RAM, allowing systems to run programs larger than available memory size using **paging**.\n\n"
                     "💡 *Core Mechanisms*:\n"
                     "- Logical memory is divided into fixed-size chunks called **pages**. Physical RAM is divided into **frames**.\n"
                     "- **Page Table**: Keeps mapping coordinates from virtual pages to physical frames.\n"
                     "- **Page Fault**: Exception raised by hardware when a page referenced by virtual address is not loaded in physical RAM, forcing OS to retrieve it from disk storage.\n\n"
                     "🎓 *Interview Tip*: Explain how the Translation Lookaside Buffer (TLB) speeds page lookups. It is a high-speed hardware cache of page table entries.",
            "follow_up": ["Explain OS Deadlocks", "Explain Process vs Thread", "Explain TCP vs UDP"]
        },
        "tcp_vs_udp": {
            "reply": "📌 **TCP vs. UDP (Transport Layer Protocols)**:\n"
                     "- **TCP (Transmission Control Protocol)**: Connection-oriented. Guarantees reliable, ordered delivery of packets using handshakes (3-way SYN/ACK), flow control, congestion controls, and retransmissions.\n"
                     "- **UDP (User Datagram Protocol)**: Connectionless. Sends packets ('datagrams') directly without verification. Low overhead, fast speed, but no delivery or ordering guarantee.\n\n"
                     "🛠 *Comparison Grid*:\n"
                     "- **TCP**: Used for HTTP/HTTPS, Email (SMTP), File Transfer (FTP), SSH.\n"
                     "- **UDP**: Used for Live Video Streaming (VoIP), Online Gaming, DNS lookups.\n\n"
                     "🎓 *Interview Tip*: Describe the **TCP 3-Way Handshake**: Client sends `SYN`, Server responds with `SYN-ACK`, Client replies with `ACK`. Connection is now established.",
            "follow_up": ["Explain HTTP vs HTTPS", "Describe DNS", "Explain Virtual Memory & Page Faults"]
        },
        "http_vs_https": {
            "reply": "📌 **HTTP vs. HTTPS (Network Security)**:\n"
                     "- **HTTP**: Hypertext Transfer Protocol. Transmits data in plaintext. Vulnerable to sniffing and man-in-the-middle attacks.\n"
                     "- **HTTPS**: HTTP over SSL/TLS. Encrypts all request and response payloads, ensuring privacy, data integrity, and authentication.\n\n"
                     "💡 *Key Revision Points*:\n"
                     "- Encryption: HTTPS uses asymmetric cryptography (public key) to exchange symmetric keys (private key) for session encryption.\n"
                     "- Port: HTTP runs over port 80; HTTPS runs over port 443.\n"
                     "🎓 *Interview Tip*: Explain that HTTPS requires an SSL/TLS Certificate signed by a trusted Certificate Authority (CA) to authenticate server identity.",
            "follow_up": ["Explain TCP vs UDP", "Describe DNS", "Explain JWT Authentication"]
        },
        "dns": {
            "reply": "📌 **Domain Name System (DNS) Mechanics**:\n"
                     "DNS translates human-readable hostnames (e.g. `google.com`) into physical IP addresses (e.g. `142.250.190.46`).\n\n"
                     "💡 *Resolution Steps*:\n"
                     "1. **Browser Cache**: Check local DNS records.\n"
                     "2. **Recursive Resolver**: Query Internet Service Provider resolver.\n"
                     "3. **Root Nameserver**: Points to Top-Level Domain (TLD) server (like `.com`).\n"
                     "4. **TLD Server**: Points to Authoritative Nameserver.\n"
                     "5. **Authoritative Nameserver**: Returns the actual IP address to browser.\n\n"
                     "🎓 *Interview Tip*: Mention DNS caching at recursive resolvers and TTL (Time to Live) parameters which specify how long records remain valid.",
            "follow_up": ["Explain HTTP vs HTTPS", "Explain TCP vs UDP", "Explain REST APIs"]
        },
        "time_complexity": {
            "reply": "📌 **Time Complexity & Big O Notation**:\n"
                     "Big O notation characterizes execution times or space overheads of algorithms as inputs (N) scale up, evaluating worst-case behavior:\n"
                     "- **O(1)**: Constant time (e.g. Hash Map lookup).\n"
                     "- **O(log N)**: Logarithmic time (e.g. Binary Search, B-Tree lookup).\n"
                     "- **O(N)**: Linear time (e.g. iterating an array list).\n"
                     "- **O(N log N)**: Log-linear time (e.g. Merge Sort, Quick Sort average).\n"
                     "- **O(N²)**: Quadratic time (e.g. nested loops, Bubble Sort).\n\n"
                     "🛠 *Code Example*:\n"
                     "```javascript\n"
                     "// Two independent loops = O(N) + O(M) = O(N + M)\n"
                     "for (let i = 0; i < N; i++) { ... }\n"
                     "for (let j = 0; j < M; j++) { ... }\n"
                     "```\n\n"
                     "🎓 *Interview Tip*: Always analyze both time complexity (loops, recursive calls) and space complexity (extra buffers, call stack frames).",
            "follow_up": ["Explain Database Indexing", "Explain OS Deadlocks", "Explain Virtual DOM"]
        },
        "star_framework": {
            "reply": "📌 **STAR Behavioral Interview Framework**:\n"
                     "Structure your answers to situational questions (e.g., 'Tell me about a time you failed') using the STAR format:\n"
                     "- **S (Situation)**: Set the context. Describe the challenge or project briefly.\n"
                     "- **T (Task)**: Detail your responsibility or what needed to be achieved.\n"
                     "- **A (Action)**: Explain the specific steps *you* took to address the problem. Emphasize your technical decisions.\n"
                     "- **R (Result)**: Share the positive outcome, backed by metrics if possible (e.g., speed increases, lower error rate).\n\n"
                     "💡 *Key Tip*: Keep Situation and Task at 20% of your answer. Spend 60% on your Actions, and 20% on the Results.",
            "follow_up": ["Improve my resume guidelines", "Rehearse mock interview questions", "Show career domain timlines"]
        },
        "resume_tips": {
            "reply": f"📌 **Resume Optimization Audit**:\n"
                     f"Your current profile has {len(skills)} skills captured, with CGPA set to {profile.gpa or 'N/A'}.\n\n"
                     f"💡 *Actionable Improvements*:\n"
                     f"- **Technical Alignment**: Make sure {top_skill} is prominent. Include trending keywords (Docker, REST APIs) in your description.\n"
                     f"- **Metrics Integration**: Instead of 'built features', write 'designed database queries reducing load time by 30%'.\n"
                     f"- **Skills Density**: Incorporate role-aligned skills (e.g. {missing_skill}) to bypass ATS keyword filters.\n"
                     f"- **PDF Upload**: Ensure you have uploaded your latest resume in the Dashboard Overview.",
            "follow_up": ["Show me my weakest skill area", "Compare me with peers", "STAR Framework tips"]
        },
        "gpa_tips": {
            "reply": f"📌 **CGPA Impact Analysis**:\n"
                     f"Your saved CGPA is **{profile.gpa or 'Not set'}**.\n\n"
                     f"- **CGPA >= 8.0**: Highly competitive. You meet auto-shortlist filters for elite placements. Keep coding projects strong.\n"
                     f"- **CGPA 7.0 - 8.0**: Solid. You are eligible for 80% of hiring companies. Focus on highlighting strong technical skills and project descriptions.\n"
                     f"- **CGPA < 7.0**: Focus heavily on full-stack projects, AI reviews, and interview performance logs. Strong project auditor scorecards help bypass hard GPA filters during interviews.",
            "follow_up": ["Show me my weakest skill area", "Explain Database Indexing", "Compare me with peers"]
        },
        "skills_gap": {
            "reply": f"📌 **Technical Stack Skill Audit**:\n"
                     f"Your current skills: {', '.join(skills) if skills else 'No skills listed yet'}.\n\n"
                     f"💡 *Recommended Additions*:\n"
                     f"- Market demand is high for **{missing_skill}**. Adding it will improve your placement matching odds.\n"
                     f"- Acquire skills by completing actions in your active **AI Career Roadmap** tab.\n"
                     f"- Validate your projects in the **AI Project Auditor** to check implementation quality.",
            "follow_up": ["Show career domain timelines", "Show me my weakest skill area", "Explain Database Indexing"]
        },
        "project_architecture": {
            "reply": "📌 **Project Architecture Design Patterns**:\n"
                     "- **MVC (Model-View-Controller)**: Divides application logic into Data structures (Model), user interface templates (View), and routing logic (Controller).\n"
                     "- **Microservices**: Decomposes systems into independent, self-contained services communicating via API endpoints or messaging queues. Highly scalable but complex.\n"
                     "- **Monolith**: Single unified database and codebase server. Easy to build, test, and deploy initially; harder to scale as teams grow.\n\n"
                     "💡 *Revision Checklist*:\n"
                     "- Ensure API endpoints are structured statelessly.\n"
                     "- Use connection pools for databases to handle peak request volumes.\n"
                     "- Secure keys and database secrets in `.env` configuration files.",
            "follow_up": ["Explain REST APIs", "Explain Database Indexing", "Explain Database Normalization"]
        }
    }

    matched_key = None
    for key in kb_rules:
        if any(word in text for word in kb_rules[key]):
            matched_key = key
            break

    if matched_key and matched_key in kb:
        return kb[matched_key]

    if any(word in text for word in ["hello", "hi", "hey", "start", "introduce"]):
        return {
            "reply": "🤖 **Greetings! I am your AI Career Mentor.**\n\n"
                     "I can explain core CS concepts (Virtual DOM, Normalization, TCP/UDP, Deadlocks, etc.), "
                     "audit your resume and skills, or help you prepare for technical interviews. Ask me a specific question!",
            "follow_up": ["Improve my resume guidelines", "Show career domain timelines", "Explain Database Indexing"]
        }

    strengths_logs = build_resume_weakness_detector(profile)
    weakness_msg = strengths_logs["weaknesses"][0] if strengths_logs["weaknesses"] else "none"

    return {
        "reply": f"🤖 **AI Career Mentor Feedback**:\n\n"
                 f"I've analyzed your question and cross-referenced it with your student profile.\n\n"
                 f"To optimize your career preparedness, focus on acquiring **{missing_skill}** to cover market gaps. "
                 f"Our audits indicate your most critical profile warning is: *'{weakness_msg}'*.\n\n"
                 f"Ask me about specific technical topics (e.g. *'Explain database normalization'* or *'How does indexing work'*) and I will give you a step-by-step breakdown!",
        "follow_up": [
            "Show career domain timelines",
            "Show me my weakest skill area",
            "Compare me with peers"
        ]
    }


def build_peer_comparison(profile: StudentProfile) -> dict:
    student_skills = set(_normalize_skills(_student_skill_names(profile)))
    all_students = StudentProfile.query.all()
    total_peers = len(all_students)
    
    if total_peers <= 1:
        avg_gpa = profile.gpa or 7.5
        avg_skills = len(student_skills) or 3
        percentile = 85.0
    else:
        gpas = [s.gpa for s in all_students if s.gpa is not None]
        avg_gpa = round(sum(gpas) / len(gpas), 2) if gpas else 7.5
        skill_counts = [len(s.skills) for s in all_students]
        avg_skills = round(sum(skill_counts) / len(skill_counts), 1) if skill_counts else 3.0
        
        your_gpa = profile.gpa or 0.0
        peers_below = sum(1 for g in gpas if g <= your_gpa)
        percentile = round((peers_below / len(gpas)) * 100, 1) if gpas else 75.0

    return {
        "percentile_rank": f"Top {max(1, int(100 - percentile))}%",
        "cgpa_comparison": {
            "your_cgpa": profile.gpa,
            "peer_average_cgpa": avg_gpa,
            "status": "Above Average" if (profile.gpa or 0) >= avg_gpa else "Focus on Skill Depth"
        },
        "skill_count_comparison": {
            "your_skills": len(student_skills),
            "peer_average_skills": avg_skills,
        },
        "total_peers": total_peers,
    }


def build_interview_simulation(profile: StudentProfile) -> dict:
    skills = _normalize_skills(_student_skill_names(profile))
    top_skill = skills[0].title() if skills else "Full-Stack Development"
    return {
        "recommended_role": f"{top_skill} Engineer",
        "mock_questions_count": 5,
        "readiness_score": 82,
        "tips": [
            "Practice explaining your project architecture out loud using the STAR method.",
            "Review database indexing and normalization before technical screening rounds.",
            "Be prepared to code live algorithms or explain system design trade-offs."
        ]
    }


def build_student_intelligence_dashboard(profile: StudentProfile) -> dict:
    return {
        "demand_hiring_analyzer": build_demand_hiring_analyzer(profile),
        "resume_weakness_detector": build_resume_weakness_detector(profile),
        "peer_comparison_dashboard": build_peer_comparison(profile),
        "interview_simulation": build_interview_simulation(profile),
    }
