from faker import Faker
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import generate_password_hash

from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.db.models import User
from zimfarm_backend.db.user import check_user_permission


def test_check_permission_from_role(dbsession: OrmSession, data_gen: Faker):
    user = User(
        username=data_gen.first_name(),
        password_hash=generate_password_hash("testpassword"),
        email=data_gen.safe_email(),
        scope=None,
        role=RoleEnum.EDITOR,
    )
    dbsession.add(user)
    # editors can create schedules but can't create tasks
    assert check_user_permission(user, namespace="schedules", name="create") is True
    assert check_user_permission(user, namespace="tasks", name="create") is False


def test_check_permission_from_custom_scope(dbsession: OrmSession, data_gen: Faker):
    user = User(
        username=data_gen.first_name(),
        password_hash=generate_password_hash("testpassword"),
        email=data_gen.safe_email(),
        scope={
            "zim": {"upload": True},
            "tasks": {
                "cancel": True,
                "create": True,
                "delete": False,
                "update": True,
            },
        },
        role="custom",
    )
    dbsession.add(user)
    assert check_user_permission(user, namespace="schedules", name="read") is False
    assert check_user_permission(user, namespace="zim", name="upload") is True
