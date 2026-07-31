from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import User, UserRole, StudentProfile, CompanyProfile
from app.utils.api import APIError

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or data.get("name") or "").strip()
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
    if username and User.query.filter_by(username=username).first():
        raise APIError("Username already taken", 409, "conflict")

    user = User(email=email, username=username, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.flush()

    if role == UserRole.STUDENT.value:
        profile = StudentProfile(
            user_id=user.id,
            full_name=username or email.split("@")[0],
            gpa=0.0,
            education="Not Specified"
        )
        db.session.add(profile)
    elif role == UserRole.COMPANY.value:
        profile = CompanyProfile(
            user_id=user.id,
            company_name=username or email.split("@")[0],
            description="New Company",
            website_url=""
        )
        db.session.add(profile)

    db.session.commit()

    return jsonify({"message": "User registered", "user_id": user.id, "username": username}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email_or_username = (data.get("email") or data.get("username") or "").strip().lower()
    password = data.get("password")

    if not email_or_username or not password:
        raise APIError("email/username and password are required", 422, "validation_error")

    user = User.query.filter_by(email=email_or_username).first()
    if not user:
        user = User.query.filter_by(username=email_or_username).first()

    if not user or not check_password_hash(user.password_hash, password or ""):
        raise APIError("Invalid credentials", 401, "invalid_credentials")

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    display_name = user.username or user.email
    if user.role == UserRole.STUDENT.value and user.student_profile:
        display_name = user.student_profile.full_name
    elif user.role == UserRole.COMPANY.value and user.company_profile:
        display_name = user.company_profile.company_name
    return jsonify({"access_token": token, "role": user.role, "user_id": user.id, "username": display_name})
