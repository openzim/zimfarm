from typing import Optional
from bson import ObjectId
from datetime import datetime
import pytest


@pytest.fixture(scope='module')
def make_schedule():
    def _make_schedule(name: str):
        return {'_id': ObjectId(), 'name': name}
    return _make_schedule


@pytest.fixture(scope='module')
def make_event():
    def _make_event(code: str, timestamp: datetime, **kwargs):
        return {'code': code, 'timestamp': timestamp}.update(kwargs)
    return _make_event


@pytest.fixture(scope='module')
def make_task(make_schedule, make_event):
    task_ids = []

    def _make_task(schedule_name: str = 'test_schedule'):
        task = {'schedule': make_schedule(schedule_name),
                'status': 'started',
                'events': [
                    make_event('started', datetime.now())
                ]}
