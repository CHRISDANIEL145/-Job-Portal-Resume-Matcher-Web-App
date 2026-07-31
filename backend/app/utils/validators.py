from __future__ import annotations

from app.utils.api import APIError


def parse_optional_gpa(value):
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise APIError("gpa must be a number", 422, "validation_error") from exc

    if parsed < 0 or parsed > 10:
        raise APIError("gpa must be between 0 and 10", 422, "validation_error")
    return parsed


def parse_skill_list(value):
    if value is None:
        return []

    if not isinstance(value, list):
        raise APIError("skills must be an array of strings", 422, "validation_error")

    cleaned: list[str] = []
    seen = set()
    for item in value:
        if not isinstance(item, str):
            raise APIError("skills must contain only strings", 422, "validation_error")
        normalized = item.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            cleaned.append(normalized)
    return cleaned


def parse_pagination_args(request, default_per_page: int = 20, max_per_page: int = 100):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", default_per_page, type=int)

    if page < 1:
        raise APIError("page must be >= 1", 422, "validation_error")
    if per_page < 1 or per_page > max_per_page:
        raise APIError(
            f"per_page must be between 1 and {max_per_page}",
            422,
            "validation_error",
        )
    return page, per_page
