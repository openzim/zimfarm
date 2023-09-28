import db.models as dbm
from common.enum import TaskStatus
from common.utils import task_event_handler
from db import Session


class TestTaskEvents:
    def test_task_event_reserved(self, temp_schedule, make_task, worker):
        task = make_task(schedule_name=temp_schedule["name"])
        with Session.begin() as session:
            schedule = dbm.Schedule.get(session, temp_schedule["name"])
            assert schedule.most_recent_task_id is None
            task_event_handler(
                session, task["_id"], TaskStatus.reserved, {"worker": worker["name"]}
            )
            assert schedule.most_recent_task_id == task["_id"]

    def test_task_event_started(self, temp_schedule, make_task, worker):
        task = make_task(schedule_name=temp_schedule["name"])
        with Session.begin() as session:
            schedule = dbm.Schedule.get(session, temp_schedule["name"])
            assert schedule.most_recent_task_id is None
            task_event_handler(session, task["_id"], TaskStatus.started, {})
            assert schedule.most_recent_task_id is None
