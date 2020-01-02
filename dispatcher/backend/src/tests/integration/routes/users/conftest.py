from common.roles import ROLES

import pytest
from bson import ObjectId


@pytest.fixture(scope="module")
def make_user(database):
    user_ids = []

    def _make_user(username: str = "some-user", role: str = None) -> dict:
        document = {
            "_id": ObjectId(),
            "username": username,
        }
        if role:
            document["scope"] = ROLES.get(role)
        user_id = database.users.insert_one(document).inserted_id
        user_ids.append(user_id)
        return document

    yield _make_user

    database.users.delete_many({"_id": {"$in": user_ids}})


@pytest.fixture(scope="module")
def user(make_user):
    return make_user()


@pytest.fixture(scope="module")
def users(make_user):
    users = []
    for index in range(5):
        username = "user_{}".format(index)
        user = make_user(username)
        users.append(user)
    return users
