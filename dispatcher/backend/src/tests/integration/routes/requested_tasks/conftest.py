import uuid
from datetime import datetime

import pytest
from bson import ObjectId

from common.enum import TaskStatus
from common.mongo import RequestedTasks


@pytest.fixture()
def make_event():
    def _make_event(code: str, timestamp: datetime, **kwargs):
        event = {"code": code, "timestamp": timestamp}
        event.update(kwargs)
        return event

    return _make_event


@pytest.fixture()
def make_requested_task(database, make_event):
    requested_task_ids = []
    requested_tasks = RequestedTasks(database=database)

    def _make_requested_task(
        schedule_id=ObjectId(),
        schedule_name="",
        status=TaskStatus.requested,
        hostname="zimfarm_worker.com",
        requested_by="someone",
        priority=0,
    ):
        events = [TaskStatus.requested]
        timestamp = {event: datetime.now() for event in events}
        events = [make_event(event, timestamp[event]) for event in events]

        config = {
            "flags": {"api-key": "aaaaaa", "id": "abcde", "type": "channel"},
            "image": {"name": "openzim/youtube", "tag": "latest"},
            "task_name": "youtube",
            "warehouse_path": "/other",
            "resources": {"cpu": 3, "memory": 1024, "disk": 1024},
        }

        requested_task = {
            "_id": ObjectId(),
            "status": status,
            "schedule_name": schedule_name,
            "timestamp": timestamp,
            "events": events,
            "config": config,
            "priority": priority,
            "requested_by": requested_by,
        }

        requested_tasks.insert_one(requested_task)
        requested_task_ids.append(requested_task["_id"])
        return requested_task

    yield _make_requested_task

    requested_tasks.delete_many({"_id": {"$in": requested_task_ids}})


@pytest.fixture()
def requested_tasks(make_requested_task):
    tasks = []
    for i in range(5):
        tasks += [
            make_requested_task(status=TaskStatus.requested),
            make_requested_task(status=TaskStatus.reserved),
            make_requested_task(status=TaskStatus.started),
            make_requested_task(status=TaskStatus.succeeded),
            make_requested_task(status=TaskStatus.failed),
        ]
    return tasks


@pytest.fixture()
def requested_task(make_requested_task):
    return make_requested_task()


@pytest.fixture()
def schedule(make_schedule):
    return make_schedule(name=uuid.uuid4().hex)
