from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import User, UserRole
from app.utils.api import APIError


def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            identity = get_jwt_identity()
            user = User.query.get(int(identity))
            if not user:
                raise APIError("User not found", 404, "not_found")
            if user.role not in [r.value if isinstance(r, UserRole) else r for r in roles]:
                raise APIError("Unauthorized role", 403, "forbidden")
            return fn(*args, **kwargs)

        return decorated

    return wrapper
