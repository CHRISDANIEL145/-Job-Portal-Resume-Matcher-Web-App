from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import User, UserRole
from app.utils.api import APIError

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    role = (data.get("role") or "").strip().lower()
    valid_roles = [r.value for r in UserRole]

    if not email or not password or role not in valid_roles:
        raise APIError("email, password, and valid role are required", 422, "validation_error")
    if len(password) < 6:
        raise APIError("password must be at least 6 characters", 422, "validation_error")

    if User.query.filter_by(email=email).first():
        raise APIError("Email already exists", 409, "conflict")

    user = User(email=email, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered", "user_id": user.id}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not password:
        raise APIError("email and password are required", 422, "validation_error")

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password or ""):
        raise APIError("Invalid credentials", 401, "invalid_credentials")

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"access_token": token, "role": user.role, "user_id": user.id})
