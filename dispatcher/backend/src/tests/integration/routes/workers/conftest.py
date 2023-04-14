import datetime

import pytest
import sqlalchemy as sa

import db.models as dbm
from common import getnow
from db import Session


@pytest.fixture(scope="module")
def make_worker(make_user):
    worker_ids = []

    def _make_worker(
        name: str = "worker_name",
        username: str = "some-user",
        last_seen: datetime = getnow(),
        resources: dict = None,
        last_ip: str = "192.168.1.1",
    ) -> dict:
        with Session.begin() as session:
            user_id = dbm.User.get_id_or_none(session, username)
            if user_id is None:
                make_user(username)
                user_id = dbm.User.get_id_or_none(session, username)
            worker = dbm.Worker(
                mongo_val=None,
                mongo_id=None,
                name=name,
                selfish=False,
                cpu=3,
                memory=1024,
                disk=1024,
                offliners=["mwoffliner", "youtube"],
                platforms={},
                last_seen=last_seen,
                last_ip=last_ip,
            )
            worker.user_id = user_id
            session.add(worker)
            session.flush()
            worker_id = worker.id
            worker_ids.append(worker_id)
            document = {
                "name": worker.name,
                "username": worker.user.username,
                "offliners": worker.offliners,
                "last_seen": worker.last_seen,
                "last_ip": worker.last_ip,
                "resources": {
                    "cpu": worker.cpu,
                    "disk": worker.disk,
                    "memory": worker.memory,
                },
            }
        return document

    yield _make_worker

    with Session.begin() as session:
        for worker in session.execute(
            sa.select(dbm.Worker).where(dbm.Worker.id.in_(worker_ids))
        ).scalars():
            session.delete(worker)


@pytest.fixture(scope="module")
def worker(make_worker):
    return make_worker()


@pytest.fixture(scope="module")
def workers(make_worker, make_config, make_language):
    workers = []
    for index in range(38):
        name = f"worker_{index}"
        username = (
            f"user_{index%2}"  # build some users as well but not as many as workers
        )
        last_ip = f"192.168.1.{index}"
        worker = make_worker(name, username=username, last_ip=last_ip)
        workers.append(worker)
    return workers
