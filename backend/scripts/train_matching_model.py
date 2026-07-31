import argparse
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.matching import _heuristic_matching_score, similarity_score
from app.services.ml_matching import build_feature_map, save_model_bundle, train_classifier
from app.services.resume_parser import SKILL_ALIASES


def _sample_skills(skill_pool: list[str], min_count: int, max_count: int) -> list[str]:
    count = random.randint(min_count, max_count)
    return random.sample(skill_pool, k=min(count, len(skill_pool)))


def _build_training_dataset(sample_size: int) -> tuple[list[dict[str, float]], list[int]]:
    skill_pool = sorted(SKILL_ALIASES.keys())
    features = []
    labels = []

    for _ in range(sample_size):
        student_skills = _sample_skills(skill_pool, 1, 12)
        job_skills = _sample_skills(skill_pool, 2, 10)

        student_gpa = round(random.uniform(5.0, 10.0), 2) if random.random() > 0.15 else None
        min_gpa = round(random.uniform(6.0, 9.5), 2) if random.random() > 0.2 else None

        priority_skills = []
        if random.random() > 0.35:
            max_priority = min(4, len(student_skills))
            priority_skills = random.sample(student_skills, k=random.randint(1, max_priority))

        skill_sim = similarity_score(student_skills, job_skills)
        feature_map = build_feature_map(
            skill_similarity=skill_sim,
            student_skills=student_skills,
            job_skills=job_skills,
            student_gpa=student_gpa,
            min_gpa=min_gpa,
            priority_skills=priority_skills,
        )
        features.append(feature_map)

        baseline_score = _heuristic_matching_score(
            student_skills,
            job_skills,
            student_gpa,
            min_gpa,
            priority_skills=priority_skills,
        )

        # Add controlled noise so the model learns a smoother probability surface.
        probability = max(0.0, min((baseline_score - 42.0) / 35.0, 1.0))
        label = 1 if random.random() <= probability else 0
        labels.append(label)

    if len(set(labels)) < 2:
        midpoint = len(labels) // 2
        labels[:midpoint] = [0] * midpoint
        labels[midpoint:] = [1] * (len(labels) - midpoint)

    return features, labels


def main():
    parser = argparse.ArgumentParser(description="Train and save matching model bundle")
    parser.add_argument("--samples", type=int, default=5000, help="Synthetic training sample count")
    parser.add_argument(
        "--output",
        type=str,
        default="app/ml_artifacts/matching_model.joblib",
        help="Output path for trained model bundle",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)

    features, labels = _build_training_dataset(sample_size=max(args.samples, 1000))
    model_bundle = train_classifier(features, labels, random_state=args.seed)
    save_model_bundle(model_bundle, args.output)

    metrics = model_bundle["metrics"]
    print("Training complete")
    print(f"Samples: {len(features)}")
    print(f"Accuracy: {metrics['accuracy']}")
    print(f"F1: {metrics['f1']}")
    print(f"ROC-AUC: {metrics['roc_auc']}")
    print(f"Model saved to: {args.output}")


if __name__ == "__main__":
    main()
