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
    ) -> dict:
        document = {
            "_id": ObjectId(),
            "name": name,
            "username": username,
            "offliners": ["mwoffliner", "youtube"],
            "last_seen": last_seen,
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
        worker = make_worker(name)
        workers.append(worker)
    return workers
