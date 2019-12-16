from datetime import datetime

import pytest
from bson import ObjectId

from common.enum import TaskStatus
from common.mongo import Tasks, RequestedTasks


@pytest.fixture()
def make_event():
    def _make_event(code: str, timestamp: datetime, **kwargs):
        event = {"code": code, "timestamp": timestamp}
        event.update(kwargs)
        return event

    return _make_event


@pytest.fixture()
def make_task(database, make_event):
    task_ids = []
    tasks = Tasks(database=database)

    def _make_task(
        schedule_id=ObjectId(),
        schedule_name="",
        status=TaskStatus.succeeded,
        hostname="zimfarm_worker.com",
    ):
        if status == TaskStatus.requested:
            events = [TaskStatus.requested]
        elif status == TaskStatus.reserved:
            events = [TaskStatus.requested, TaskStatus.reserved]
        elif status == TaskStatus.started:
            events = [TaskStatus.requested, TaskStatus.reserved, TaskStatus.started]
        elif status == TaskStatus.succeeded:
            events = [
                TaskStatus.requested,
                TaskStatus.reserved,
                TaskStatus.started,
                TaskStatus.succeeded,
            ]
        else:
            events = [
                TaskStatus.requested,
                TaskStatus.reserved,
                TaskStatus.started,
                TaskStatus.failed,
            ]

        timestamp = {event: datetime.now() for event in events}
        events = [make_event(event, timestamp[event]) for event in events]
        container = {
            "command": "mwoffliner --mwUrl=https://example.com",
            "image": {"name": "mwoffliner", "tag": "1.8.0"},
            "exit_code": 0,
            "stderr": "example_stderr",
            "stdout": "example_stdout",
        }
        debug = {"args": [], "kwargs": {}}

        if status == TaskStatus.failed:
            debug["exception"] = "example_exception"
            debug["traceback"] = "example_traceback"
            files = {}
        else:
            files = {"mwoffliner_1．zim": {"name": "mwoffliner_1.zim", "size": 1000}}

        task = {
            "_id": ObjectId(),
            "status": status,
            "worker": hostname,
            "schedule_name": schedule_name,
            "timestamp": timestamp,
            "events": events,
            "container": container,
            "debug": debug,
            "files": files,
        }

        tasks.insert_one(task)
        task_ids.append(task["_id"])
        return task

    yield _make_task

    tasks.delete_many({"_id": {"$in": task_ids}})


@pytest.fixture()
def tasks(make_task):
    tasks = []
    for i in range(5):
        tasks += [
            make_task(status=TaskStatus.requested),
            make_task(status=TaskStatus.reserved),
            make_task(status=TaskStatus.started),
            make_task(status=TaskStatus.succeeded),
            make_task(status=TaskStatus.failed),
        ]
    return tasks


@pytest.fixture()
def task(make_task):
    return make_task(status=TaskStatus.succeeded)


@pytest.fixture()
def make_requested_task(database, make_event):
    requested_task_ids = []
    requested_tasks = RequestedTasks(database=database)

    def _make_requested_task(
        schedule_id=ObjectId(),
        schedule_name="",
        status=TaskStatus.requested,
        hostname="zimfarm_worker.com",
    ):
        events = [TaskStatus.requested]
        timestamp = {event: datetime.now() for event in events}
        events = [make_event(event, timestamp[event]) for event in events]

        config = {
            "config": {
                "flags": {"api-key": "aaaaaa", "id": "abcde", "type": "channel"},
                "image": {"name": "openzim/youtube", "tag": "latest"},
                "task_name": "youtube",
                "warehouse_path": "/other",
            }
        }

        requested_task = {
            "_id": ObjectId(),
            "status": status,
            "schedule_name": schedule_name,
            "timestamp": timestamp,
            "events": events,
            "config": config,
        }

        requested_tasks.insert_one(requested_task)
        requested_task_ids.append(requested_task["_id"])
        return requested_task

    yield _make_requested_task

    requested_tasks.delete_many({"_id": {"$in": requested_task_ids}})


@pytest.fixture()
def requested_task(make_requested_task):
    return make_requested_task()
