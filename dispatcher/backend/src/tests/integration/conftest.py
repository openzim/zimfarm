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
def make_access_token():
    def _make_access_token(username: str, role: str = "editor"):
        token = LoadedAccessToken(uuid4(), username, ROLES.get(role)).encode()
        return "Bearer {}".format(token)

    yield _make_access_token


@pytest.fixture(scope="session")
def access_token(make_access_token):
    yield make_access_token("username", "admin")


@pytest.fixture(scope="session")
def database() -> mongo.Database:
    yield mongo.Database()


class GarbageCollector:
    worker_ids = []
    schedule_ids = []
    task_ids = []
    requested_task_ids = []
    user_ids = []

    def add_worker_id(self, worker_id):
        self.worker_ids.append(worker_id)

    def add_schedule_id(self, schedule_id):
        self.schedule_ids.append(schedule_id)

    def add_task_id(self, task_id):
        self.task_ids.append(task_id)

    def add_requested_task_id(self, requested_task_id):
        self.requested_task_ids.append(requested_task_id)

    def add_user_id(self, user_id):
        self.user_ids.append(user_id)

    def collect(self):
        with Session.begin() as session:
            for schedule in session.execute(
                sa.select(dbm.Schedule).where(dbm.Schedule.id.in_(self.schedule_ids))
            ).scalars():
                schedule.most_recent_task = None
                session.delete(schedule)
            for user in session.execute(
                sa.select(dbm.User).where(dbm.User.id.in_(self.user_ids))
            ).scalars():
                session.delete(user)
            for worker in session.execute(
                sa.select(dbm.Worker).where(dbm.Worker.id.in_(self.worker_ids))
            ).scalars():
                session.delete(worker)
            for task in session.execute(
                sa.select(dbm.Task).where(dbm.Task.id.in_(self.task_ids))
            ).scalars():
                session.delete(task)
            for requested_task in session.execute(
                sa.select(dbm.RequestedTask).where(
                    dbm.RequestedTask.id.in_(self.requested_task_ids)
                )
            ).scalars():
                session.delete(requested_task)


@pytest.fixture(scope="module")
def garbage_collector() -> GarbageCollector:
    gc = GarbageCollector()
    yield gc
    gc.collect()


@pytest.fixture()
def cleanup_create_test():
    """Utility fixture to delete resources that may have been created during a test.
    These resources have to be deleted based on their name since the code / test may
    have failed at any point after their creation.
    We assume that 'normal' resources created by other fixtures do not have a name
    ending with 'create_test' and that resources created during creation tests have a
    name ending with 'create_test'.
    """

    yield "whatever"

    with Session.begin() as session:
        for schedule in session.execute(
            sa.select(dbm.Schedule).where(dbm.Schedule.name.endswith("_create_test"))
        ).scalars():
            schedule.most_recent_task = None
            session.delete(schedule)
        for worker in session.execute(
            sa.select(dbm.Worker).where(dbm.Worker.name.endswith("_create_test"))
        ).scalars():
            session.delete(worker)
        for user in session.execute(
            sa.select(dbm.User).where(dbm.User.username.endswith("_create_test"))
        ).scalars():
            session.delete(user)


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    Initializer.check_if_schema_is_up_to_date()
