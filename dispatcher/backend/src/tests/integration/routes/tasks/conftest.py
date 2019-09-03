from datetime import datetime

import pytest
from bson import ObjectId

from common.entities import TaskStatus
from common.mongo import Tasks


@pytest.fixture()
def make_event():
    def _make_event(code: str, timestamp: datetime, **kwargs):
        event = {'code': code, 'timestamp': timestamp}
        event.update(kwargs)
        return event
    return _make_event


@pytest.fixture()
def make_task(database, make_event):
    task_ids = []
    tasks = Tasks(database=database)

    def _make_task(schedule_id=ObjectId(), schedule_name='', status=TaskStatus.succeeded,
                   hostname='username@zimfarm_worker.com'):
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

        schedule = {'_id': schedule_id, 'name': schedule_name}
        timestamp = {event: datetime.now() for event in events}
        events = [make_event(event, timestamp[event]) for event in events]
        container = {
            'command': 'mwoffliner --mwUrl=https://example.com',
            'image': {'name': 'mwoffliner', 'tag': '1.8.0'},
            'exit_code': 0,
            'stderr': 'example_stderr',
            'stdout': 'example_stdout'
        }
        debug = {
            'args': [],
            'kwargs': {}
        }

        if status == TaskStatus.failed:
            debug['exception'] = 'example_exception'
            debug['traceback'] = 'example_traceback'
            files = []
        else:
            files = [{'name': 'mwoffliner_1.zim', 'size': 1000}]

        task = {
            '_id': ObjectId(),
            'status': status,
            'hostname': hostname,
            'schedule': schedule,
            'timestamp': timestamp,
            'events': events,
            'container': container,
            'debug': debug,
            'files': files
        }

        tasks.insert_one(task)
        task_ids.append(task['_id'])
        return task

    yield _make_task

    tasks.delete_many({'_id': {'$in': task_ids}})


@pytest.fixture()
def tasks(make_task):
    tasks = []
    for i in range(5):
        tasks += [
            make_task(status=TaskStatus.sent),
            make_task(status=TaskStatus.received),
            make_task(status=TaskStatus.started),
            make_task(status=TaskStatus.succeeded),
            make_task(status=TaskStatus.failed),
        ]
    return tasks


@pytest.fixture()
def task(make_task):
    return make_task(status=TaskStatus.succeeded)
