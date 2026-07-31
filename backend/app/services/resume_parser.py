import re
import fitz
import logging

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

logger = logging.getLogger(__name__)

SKILL_ALIASES = {
    "python": ["python"],
    "java": ["java"],
    "c++": ["c++", "cpp"],
    "c": ["c programming", "language c", " c "],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "reactjs", "react.js"],
    "node": ["node", "nodejs", "node.js"],
    "flask": ["flask"],
    "django": ["django"],
    "spring": ["spring", "spring boot", "springboot"],
    "sql": ["sql"],
    "mysql": ["mysql"],
    "postgresql": ["postgres", "postgresql"],
    "mongodb": ["mongodb", "mongo db"],
    "redis": ["redis"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "tailwind": ["tailwind", "tailwindcss", "tailwind css"],
    "bootstrap": ["bootstrap"],
    "git": ["git", "github", "gitlab"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "nlp": ["nlp", "natural language processing"],
    "api": ["api", "rest api", "restful api"],
    "linux": ["linux", "unix"],
}

# Build reverse lookup: skill text -> canonical name
SKILL_TEXT_TO_CANONICAL = {}
for canonical, aliases in SKILL_ALIASES.items():
    for alias in aliases:
        SKILL_TEXT_TO_CANONICAL[alias.lower()] = canonical


def _contains_phrase(text: str, phrase: str) -> bool:
    pattern = re.escape(phrase.strip().lower())
    pattern = pattern.replace(r"\ ", r"\s+")
    return re.search(rf"(?<![a-z0-9+#\.]){pattern}(?![a-z0-9+#\.])", text) is not None


def _extract_skills_with_nlp(text: str) -> set:
    """Extract skills using spaCy NER and custom matchers."""
    if not SPACY_AVAILABLE:
        return set()
    
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.warning("spaCy model 'en_core_web_sm' not installed. Install with: python -m spacy download en_core_web_sm")
        return set()
    
    doc = nlp(text)
    found = set()
    
    # Extract entities and noun chunks that match skills
    seen_texts = set()
    for token in doc:
        token_text = token.text.lower().strip()
        if token_text in SKILL_TEXT_TO_CANONICAL and token_text not in seen_texts:
            found.add(SKILL_TEXT_TO_CANONICAL[token_text])
            seen_texts.add(token_text)
    
    # Also check noun chunks for multi-word skills
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.lower().strip()
        if chunk_text in SKILL_TEXT_TO_CANONICAL:
            found.add(SKILL_TEXT_TO_CANONICAL[chunk_text])
    
    return found


class ResumeParser:
    @staticmethod
    def extract_text(pdf_path: str) -> str:
        doc = fitz.open(pdf_path)
        text = []
        for page in doc:
            text.append(page.get_text())
        doc.close()
        return "\n".join(text)

    @staticmethod
    def extract_skills(text: str) -> list[str]:
        """Extract skills using combined NLP + regex approach."""
        found = set()
        
        # 1. Try NLP-based extraction first
        nlp_skills = _extract_skills_with_nlp(text)
        found.update(nlp_skills)
        
        # 2. Fall back to regex-based keyword matching for coverage
        lower = " ".join((text or "").lower().split())
        for canonical_skill, aliases in SKILL_ALIASES.items():
            if any(_contains_phrase(lower, alias) for alias in aliases):
                found.add(canonical_skill)
        
        return sorted(found)

    @staticmethod
    def extract_education(text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        education_keywords = ["b.tech", "b.e", "bsc", "msc", "mba", "phd", "degree", "university", "college"]
        for line in lines:
            if any(keyword in line.lower() for keyword in education_keywords):
                return line
        return "Not found"

    @staticmethod
    def extract_gpa(text: str):
        normalized = " ".join((text or "").split())
        match = re.search(r"(?:gpa|cgpa)\s*[:\-]?\s*(\d+(?:\.\d+)?)", normalized, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return value if 0 <= value <= 10 else None

        fraction_match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", normalized)
        if fraction_match:
            value = float(fraction_match.group(1))
            return value if 0 <= value <= 10 else None

        return None
