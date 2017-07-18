from werkzeug.security import check_password_hash
from .models import User


def is_valid(username: str, password: str) -> bool:
    user = User.query.filter_by(username=username).first()
    return False if user is None else check_password_hash(user.password_hash, password)