from app.models import User
from app.extensions import db
from werkzeug.security import generate_password_hash


def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        return user
    return None


def create_user(name, email, password):
    if User.query.filter_by(email=email).first():
        raise ValueError(f"User with email {email} already exists.")

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
    )
    db.session.add(user)
    try:
        db.session.commit()
        return user
    except Exception:
        db.session.rollback()
        raise


def get_user_by_id(user_id):
    return User.query.get(user_id)
