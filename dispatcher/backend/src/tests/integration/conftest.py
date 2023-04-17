from uuid import uuid4

import pytest
import sqlalchemy as sa
from flask.testing import FlaskClient

import db.models as dbm
from common import mongo
from common.roles import ROLES
from db import Session
from main import application as app
from routes import API_PATH
from utils.database import Initializer
from utils.token import LoadedAccessToken

# monley-patching FlaskClient to prefix test URLs with proper API_PATH
original_get = FlaskClient.get


def rewritten_get(self, url, *args, **kwargs):
    url = f"{API_PATH}{url}"
    return original_get(self, url, *args, **kwargs)


original_post = FlaskClient.post


def rewritten_post(self, url, *args, **kwargs):
    url = f"{API_PATH}{url}"
    return original_post(self, url, *args, **kwargs)


original_put = FlaskClient.put


def rewritten_put(self, url, *args, **kwargs):
    url = f"{API_PATH}{url}"
    return original_put(self, url, *args, **kwargs)


original_patch = FlaskClient.patch


def rewritten_patch(self, url, *args, **kwargs):
    url = f"{API_PATH}{url}"
    return original_patch(self, url, *args, **kwargs)


original_delete = FlaskClient.delete


def rewritten_delete(self, url, *args, **kwargs):
    url = f"{API_PATH}{url}"
    return original_delete(self, url, *args, **kwargs)


FlaskClient.get = rewritten_get
FlaskClient.post = rewritten_post
FlaskClient.put = rewritten_put
FlaskClient.patch = rewritten_patch
FlaskClient.delete = rewritten_delete


@pytest.fixture(scope="session")
def client():
    app.testing = True
    client = app.test_client()
    yield client


@pytest.fixture(scope="session")
def access_token():
    token = LoadedAccessToken(uuid4(), "username", ROLES.get("admin")).encode()
    yield "Bearer {}".format(token)


@pytest.fixture(scope="session")
def database() -> mongo.Database:
    yield mongo.Database()


@pytest.fixture()
def cleanup_create_test():
    """Utility fixture to delete resources that may have been created during a test.
    We assume that 'normal' resources created by other fixtures do not have a name
    ending with 'create_test' and that resources created during creation tests have a
    name ending with 'create_test'.
    """

    yield "whatever"

    with Session.begin() as session:
        for sched in session.execute(
            sa.select(dbm.Schedule).where(dbm.Schedule.name.endswith("create_test"))
        ).scalars():
            session.delete(sched)


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    Initializer.check_if_schema_is_up_to_date()
