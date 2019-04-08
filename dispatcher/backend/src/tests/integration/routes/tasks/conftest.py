from datetime import datetime

import pytest
from bson import ObjectId

from common.entities import TaskStatus


@pytest.fixture()
def make_schedule():
    def _make_schedule(name: str):
        return {'_id': ObjectId(), 'name': name}
    return _make_schedule


@pytest.fixture()
def make_event():
    def _make_event(code: str, timestamp: datetime, **kwargs):
        event = {'code': code, 'timestamp': timestamp}
        event.update(kwargs)
        return event
    return _make_event


@pytest.fixture()
def make_task(database, make_schedule, make_event):
    task_ids = []

    def _make_task(schedule, status=TaskStatus.sent, hostname='username@zimfarm_worker.com'):
        if status == TaskStatus.sent:
            events = [TaskStatus.sent]
        elif status == TaskStatus.received:
            events = [TaskStatus.sent, TaskStatus.received]
        elif status == TaskStatus.started:
            events = [TaskStatus.sent, TaskStatus.received, TaskStatus.started]
        elif status == TaskStatus.succeeded:
            events = [TaskStatus.sent, TaskStatus.received, TaskStatus.started, TaskStatus.succeeded]
        else:
            events = [TaskStatus.sent, TaskStatus.received, TaskStatus.started, TaskStatus.failed]

        timestamp = {event: datetime.now() for event in events}
        events = [make_event(event, timestamp[event]) for event in events]

        task = {
            '_id': ObjectId(),
            'status': status,
            'hostname': hostname,
            'schedule': schedule,
            'timestamp': timestamp,
            'events': events}
        database.tasks.insert_one(task)
        task_ids.append(task['_id'])
        return task

    yield _make_task

    database.tasks.delete_many({'_id': {'$in': task_ids}})


@pytest.fixture()
def schedule(make_schedule):
    return make_schedule('Schedule_a')


@pytest.fixture()
def tasks(make_task, schedule):
    tasks = []
    for i in range(5):
        tasks += [
            make_task(schedule, status=TaskStatus.sent),
            make_task(schedule, status=TaskStatus.received),
            make_task(schedule, status=TaskStatus.started),
            make_task(schedule, status=TaskStatus.succeeded),
            make_task(schedule, status=TaskStatus.failed),
        ]
    return tasks


@pytest.fixture()
def task(make_task, schedule):
    return make_task(schedule, status=TaskStatus.succeeded)
