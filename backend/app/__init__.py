import os
from flask import Flask
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from .config import Config
from .extensions import db, migrate, jwt
from .routes.auth import auth_bp
from .routes.student import student_bp
from .routes.company import company_bp
from .routes.job import job_bp
from .routes.admin import admin_bp
from .routes.notification import notification_bp
from .utils.api import APIError, error_response


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f"Error creating tables: {e}")

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(student_bp, url_prefix="/api/student")
    app.register_blueprint(company_bp, url_prefix="/api/company")
    app.register_blueprint(job_bp, url_prefix="/api/jobs")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(notification_bp, url_prefix="/api/notifications")

    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        return error_response(
            message=error.message,
            status_code=error.status_code,
            code=error.code,
            details=error.details,
        )

    @app.errorhandler(404)
    def handle_404(error):
        return error_response("Resource or endpoint not found", 404, "not_found")

    @app.errorhandler(405)
    def handle_405(error):
        return error_response("Method not allowed", 405, "method_not_allowed")

    @app.errorhandler(400)
    def handle_400(error):
        return error_response("Bad request", 400, "bad_request")

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(_error):
        db.session.rollback()
        return error_response("Database operation failed", 500, "database_error")

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return error_response(str(error) or "Internal server error", 500, "internal_error")

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return error_response("Invalid token", 401, "invalid_token")

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return error_response("Token has expired", 401, "token_expired")

    @jwt.unauthorized_loader
    def unauthorized(_reason):
        return error_response("Missing authorization token", 401, "missing_token")

    @jwt.revoked_token_loader
    def revoked_token(_jwt_header, _jwt_payload):
        return error_response("Token has been revoked", 401, "revoked_token")

    @app.get("/")
    def health_check():
        return {"message": "Placement Portal API running"}

    return app
