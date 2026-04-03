from faker import Faker
from sqlalchemy.orm import Session as OrmSession
from werkzeug.security import generate_password_hash

from zimfarm_backend.common.roles import RoleEnum
from zimfarm_backend.db.account import check_account_permission
from zimfarm_backend.db.models import Account


def test_check_permission_from_role(dbsession: OrmSession, data_gen: Faker):
    username = data_gen.first_name()
    account = Account(
        username=username,
        display_name=username,
        password_hash=generate_password_hash("testpassword"),
        scope=None,
        role=RoleEnum.EDITOR,
    )
    dbsession.add(account)
    # editors can create recipes but can't create tasks
    assert check_account_permission(account, namespace="recipes", name="create") is True
    assert check_account_permission(account, namespace="tasks", name="create") is False


def test_check_permission_from_custom_scope(dbsession: OrmSession, data_gen: Faker):
    username = data_gen.first_name()
    account = Account(
        username=username,
        display_name=username,
        password_hash=generate_password_hash("testpassword"),
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
    dbsession.add(account)
    assert check_account_permission(account, namespace="recipes", name="read") is False
    assert check_account_permission(account, namespace="zim", name="upload") is True
