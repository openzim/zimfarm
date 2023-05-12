import pytest

import db.models as dbm
from common import getnow
from common.enum import TaskStatus
from db import Session
from utils.offliners import expanded_config


@pytest.fixture(scope="module")
def make_task(make_event, make_schedule, make_config, worker, garbage_collector):
    def _make_task(
        schedule_name="schedule_name",
        status=TaskStatus.succeeded,
    ):
        now = getnow()
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

        timestamp = {event: now for event in events}
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
            files = {"mwoffliner_1.zim": {"name": "mwoffliner_1.zim", "size": 1000}}
        config = expanded_config(make_config())
        with Session.begin() as session:
            worker_obj = dbm.Worker.get(session, worker["name"])
            schedule = dbm.Schedule.get(session, schedule_name, run_checks=False)
            if schedule is None:
                make_schedule(schedule_name)
                schedule = dbm.Schedule.get(session, schedule_name)
            task = dbm.Task(
                mongo_val=None,
                mongo_id=None,
                updated_at=now,
                events=events,
                debug=debug,
                status=status,
                timestamp=timestamp,
                requested_by="bob",
                canceled_by=None,
                container=container,
                priority=1,
                config=config,
                notification={},
                files=files,
                upload={},
            )
            task.schedule_id = schedule.id
            task.worker_id = worker_obj.id
            session.add(task)
            session.flush()
            garbage_collector.add_task_id(task.id)

            return {
                "_id": task.id,
                "status": task.status,
                "worker": worker_obj.name,
                "schedule_name": schedule.name,
                "timestamp": task.timestamp,
                "events": task.events,
                "container": task.container,
                "debug": task.debug,
                "files": task.files,
            }

    yield _make_task


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
def task(make_task):
    return make_task(status=TaskStatus.succeeded)
