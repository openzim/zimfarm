from werkzeug.security import generate_password_hash
from app import db
from .models import User


def add(username: str, password: str, scope: str):
    user = User(username=username,
                password_hash=generate_password_hash(password),
                scope=scope)
    db.session.add(user)
    db.session.commit()
    return user


def get(username: str) -> User:
    return User.query.filter_by(username=username).first()


def get_all(limit: int, offset: int) -> [User]:
    return User.query.limit(limit).offset(offset).all()


def change_password(username: str, password: str):
    user = get(username)
    user.password_hash = generate_password_hash(password)
    db.session.commit()
    return user


def change_scope(username: str, scope: str):
    user = get(username)
    user.scope = scope
    db.session.commit()
    return user


def delete_user(username: str):
    User.query.filter_by(username=username).delete()
    db.session.commit()
