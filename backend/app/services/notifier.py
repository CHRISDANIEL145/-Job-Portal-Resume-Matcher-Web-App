from app.extensions import db
from app.models import Notification


def create_notification(user_id: int, title: str, message: str):
    note = Notification(user_id=user_id, title=title, message=message)
    db.session.add(note)
    db.session.commit()
    return note
