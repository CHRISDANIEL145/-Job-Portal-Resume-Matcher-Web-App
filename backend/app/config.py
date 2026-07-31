import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-at-least-32-chars-long-for-security")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-at-least-32-chars-long-for-jwt-security")
    _db_url = os.getenv("DATABASE_URL", "sqlite:///placement.db")
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    MATCHING_MODEL_PATH = os.getenv(
        "MATCHING_MODEL_PATH",
        os.path.join(BASE_DIR, "ml_artifacts", "matching_model.joblib"),
    )
