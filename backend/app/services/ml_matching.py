import os
from typing import Any

from joblib import dump, load
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_COLUMNS = [
    "skill_similarity",
    "skill_overlap_ratio",
    "student_skill_count",
    "job_skill_count",
    "gpa_ratio",
    "gpa_score",
    "priority_overlap_ratio",
]

MODEL_BUNDLE_VERSION = 1


def clamp_score(value: float) -> float:
    return round(max(0.0, min(float(value), 100.0)), 2)


def _normalize_skills(skills: list[str] | None) -> list[str]:
    return sorted({str(skill).strip().lower() for skill in (skills or []) if str(skill).strip()})


def build_feature_map(
    skill_similarity: float,
    student_skills: list[str],
    job_skills: list[str],
    student_gpa,
    min_gpa,
    priority_skills: list[str] | None = None,
) -> dict[str, float]:
    normalized_student = set(_normalize_skills(student_skills))
    normalized_job = set(_normalize_skills(job_skills))
    normalized_priority = set(_normalize_skills(priority_skills))

    overlap_count = len(normalized_student.intersection(normalized_job))
    overlap_ratio = (overlap_count / len(normalized_job)) if normalized_job else 0.0

    if min_gpa is None:
        gpa_ratio = 1.0
        gpa_score = 100.0
    elif student_gpa is None:
        gpa_ratio = 0.0
        gpa_score = 0.0
    else:
        gpa_ratio = min(float(student_gpa) / float(min_gpa), 1.2)
        gpa_score = (gpa_ratio / 1.2) * 100.0

    priority_overlap = len(normalized_priority.intersection(normalized_job))
    priority_ratio = (priority_overlap / len(normalized_priority)) if normalized_priority else 0.0

    return {
        "skill_similarity": float(skill_similarity),
        "skill_overlap_ratio": round(overlap_ratio * 100.0, 2),
        "student_skill_count": float(len(normalized_student)),
        "job_skill_count": float(len(normalized_job)),
        "gpa_ratio": round(gpa_ratio, 4),
        "gpa_score": round(gpa_score, 2),
        "priority_overlap_ratio": round(priority_ratio * 100.0, 2),
    }


def to_feature_vector(feature_map: dict[str, float]) -> list[float]:
    return [float(feature_map.get(col, 0.0)) for col in FEATURE_COLUMNS]


def train_classifier(
    feature_rows: list[dict[str, float]],
    labels: list[int],
    random_state: int = 42,
) -> dict[str, Any]:
    if not feature_rows or not labels:
        raise ValueError("Training data is empty")
    if len(feature_rows) != len(labels):
        raise ValueError("Feature rows and labels must have identical length")
    if len(set(labels)) < 2:
        raise ValueError("Training labels must contain at least two classes")

    x_data = [to_feature_vector(row) for row in feature_rows]
    y_data = [int(label) for label in labels]

    x_train, x_test, y_train, y_test = train_test_split(
        x_data,
        y_data,
        test_size=0.2,
        random_state=random_state,
        stratify=y_data,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(max_iter=700, class_weight="balanced", random_state=random_state),
            ),
        ]
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)
    positive_probs = [float(row[1]) for row in probabilities]

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "f1": round(float(f1_score(y_test, predictions)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, positive_probs)), 4),
        "train_size": len(x_train),
        "test_size": len(x_test),
    }

    return {
        "version": MODEL_BUNDLE_VERSION,
        "feature_columns": FEATURE_COLUMNS,
        "model": model,
        "metrics": metrics,
    }


def predict_probability_score(
    model_bundle: dict[str, Any],
    feature_map: dict[str, float],
) -> float:
    model = model_bundle["model"]
    vector = [to_feature_vector(feature_map)]

    if hasattr(model, "predict_proba"):
        prob = float(model.predict_proba(vector)[0][1])
        return clamp_score(prob * 100.0)

    prediction = float(model.predict(vector)[0])
    return clamp_score(prediction * 100.0)


def save_model_bundle(model_bundle: dict[str, Any], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    dump(model_bundle, output_path)


def load_model_bundle(model_path: str) -> dict[str, Any]:
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    bundle = load(model_path)
    if not isinstance(bundle, dict) or "model" not in bundle:
        raise ValueError("Invalid model bundle format")
    return bundle
