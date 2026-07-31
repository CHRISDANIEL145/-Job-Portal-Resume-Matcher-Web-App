from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from flask import jsonify


@dataclass
class APIError(Exception):
    message: str
    status_code: int = 400
    code: str = "bad_request"
    details: dict[str, Any] | None = None


def error_response(
    message: str,
    status_code: int = 400,
    code: str = "bad_request",
    details: dict[str, Any] | None = None,
):
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        payload["error"]["details"] = details
    return jsonify(payload), status_code


def serialize_paginated(query, serializer: Callable[[Any], dict[str, Any]], page: int, per_page: int):
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": [serializer(item) for item in paginated.items],
        "pagination": {
            "page": paginated.page,
            "per_page": paginated.per_page,
            "pages": paginated.pages,
            "total": paginated.total,
        },
    }
