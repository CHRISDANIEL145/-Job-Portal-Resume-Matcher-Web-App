from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.extensions import db
from app.models import Notification
from app.utils.api import APIError

notification_bp = Blueprint("notification", __name__)


@notification_bp.get("")
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    notes = (
        Notification.query.filter_by(user_id=user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return jsonify([
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "read": n.read,
            "created_at": n.created_at.isoformat(),
        }
        for n in notes
    ])


@notification_bp.patch("/<int:note_id>/read")
@jwt_required()
def mark_read(note_id: int):
    user_id = int(get_jwt_identity())
    note = Notification.query.filter_by(id=note_id, user_id=user_id).first()
    if not note:
        raise APIError("Notification not found", 404, "not_found")
    note.read = True
    db.session.commit()
    return jsonify({"message": "Notification marked as read"})
