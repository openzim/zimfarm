import datetime
from typing import Any, Dict

import sqlalchemy as sa
import sqlalchemy.orm as so

import db.models as dbm
from common import getnow
from common.enum import TaskStatus
from db import Session
from utils.scheduling import request_tasks_using_schedule


class TestPeriodicScheduling:
    def get_requested_tasks_for_schedule(
        self, session: so.Session, schedule: Dict[str, Any]
    ):
        """return the list of requested tasks for a given schedule"""
        return session.execute(
            sa.select(dbm.RequestedTask).where(
                dbm.RequestedTask.schedule_id == schedule["_id"]
            )
        ).all()

    def assert_number_of_requested_tasks_for_schedule(
        self, schedule: Dict[str, Any], expected: int
    ):
        """assert that the number of requested tasks for a given schedule is expected"""
        with Session.begin() as session:
            req_tasks = self.get_requested_tasks_for_schedule(session, schedule)
            assert len(req_tasks) == expected

    def test_periodic_scheduling_simple(self, temp_schedule):
        """simple tests of periodic scheduling"""
        self.assert_number_of_requested_tasks_for_schedule(temp_schedule, 0)
        request_tasks_using_schedule()
        self.assert_number_of_requested_tasks_for_schedule(temp_schedule, 1)
        request_tasks_using_schedule()  # request again should not duplicate requests
        self.assert_number_of_requested_tasks_for_schedule(temp_schedule, 1)

    def test_periodic_scheduling_most_recent_recent(self, temp_schedule, make_task):
        """most recent task is too recent => do not request it again"""
        most_recent = make_task(temp_schedule["name"])
        now = getnow()
        with Session.begin() as session:
            task = dbm.Task.get(session, most_recent["_id"])
            task.timestamp = {
                TaskStatus.requested: now - datetime.timedelta(hours=4),
                TaskStatus.reserved: now - datetime.timedelta(hours=3, minutes=59),
                TaskStatus.started: now - datetime.timedelta(hours=3, minutes=58),
                TaskStatus.succeeded: now - datetime.timedelta(hours=1),
            }
            schedule_obj = dbm.Schedule.get(session, temp_schedule["name"])
            schedule_obj.most_recent_task = task
        self.assert_number_of_requested_tasks_for_schedule(temp_schedule, 0)
        request_tasks_using_schedule()
        self.assert_number_of_requested_tasks_for_schedule(temp_schedule, 0)

    def test_periodic_scheduling_most_recent_overdue_complete(
        self, temp_schedule, make_task
    ):
        """most recent task is overdue and not running => request a new execution"""
        most_recent = make_task(temp_schedule["name"])
        now = getnow()
        with Session.begin() as session:
            task = dbm.Task.get(session, most_recent["_id"])
            task.timestamp = {
                TaskStatus.requested: now - datetime.timedelta(days=40, hours=4),
                TaskStatus.reserved: now
                - datetime.timedelta(days=40, hours=3, minutes=59),
                TaskStatus.started: now
                - datetime.timedelta(days=40, hours=3, minutes=58),
                TaskStatus.succeeded: now - datetime.timedelta(days=40, hours=1),
            }
            schedule_obj = dbm.Schedule.get(session, temp_schedule["name"])
            schedule_obj.most_recent_task = task
        self.assert_number_of_requested_tasks_for_schedule(temp_schedule, 0)
        request_tasks_using_schedule()
        self.assert_number_of_requested_tasks_for_schedule(temp_schedule, 1)

    def test_periodic_scheduling_most_recent_overdue_running(
        self, temp_schedule, make_task
    ):
        """most recent task is overdue but still running => do not request it again"""
        most_recent = make_task(temp_schedule["name"])
        now = getnow()
        with Session.begin() as session:
            task = dbm.Task.get(session, most_recent["_id"])
            task.timestamp = {
                TaskStatus.requested: now - datetime.timedelta(days=40, hours=4),
                TaskStatus.reserved: now
                - datetime.timedelta(days=40, hours=3, minutes=59),
                TaskStatus.started: now
                - datetime.timedelta(days=40, hours=3, minutes=58),
            }
            task.status = TaskStatus.started
            schedule_obj = dbm.Schedule.get(session, temp_schedule["name"])
            schedule_obj.most_recent_task = task
        self.assert_number_of_requested_tasks_for_schedule(temp_schedule, 0)
        request_tasks_using_schedule()
        self.assert_number_of_requested_tasks_for_schedule(temp_schedule, 0)
