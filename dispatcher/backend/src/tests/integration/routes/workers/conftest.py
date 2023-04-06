import datetime

import pytest
from bson import ObjectId

from common import getnow


@pytest.fixture(scope="module")
def make_worker(database):
    worker_ids = []

    def _make_worker(
        name: str = "worker_name",
        username: str = "some-user",
        last_seen: datetime = getnow(),
        resources: dict = None,
        last_ip: str = "192.168.1.1",
    ) -> dict:
        document = {
            "_id": ObjectId(),
            "name": name,
            "username": username,
            "offliners": ["mwoffliner", "youtube"],
            "last_seen": last_seen,
            "last_ip": last_ip,
            "status": "online",
            "resources": {"cpu": 3, "memory": 1024, "disk": 1024},
        }
        worker_id = database.workers.insert_one(document).inserted_id
        worker_ids.append(worker_id)
        return document

    yield _make_worker

    database.workers.delete_many({"_id": {"$in": worker_ids}})


@pytest.fixture(scope="module")
def worker(make_worker):
    return make_worker()


@pytest.fixture(scope="module")
def workers(make_worker, make_config, make_language):
    workers = []
    for index in range(38):
        name = "worker_{}".format(index)
        last_ip = f"192.168.1.{index}"
        worker = make_worker(name, last_ip=last_ip)
        workers.append(worker)
    return workers
