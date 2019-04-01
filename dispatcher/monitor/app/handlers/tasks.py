import ast
import logging
from datetime import datetime
from typing import Optional

import pytz
from bson.objectid import ObjectId, InvalidId
from celery.events.state import Task

from entities import TaskEvent
from handlers import BaseHandler
from mongo import Tasks, Schedules

logger = logging.getLogger(__name__)


class BaseTaskEventHandler(BaseHandler):
    def __call__(self, event) -> Task:
        self.state.event(event)
        task: Task = self.state.tasks.get(event['uuid'])
        return task

    @staticmethod
    def get_task_id(task: Task) -> Optional[ObjectId]:
        try:
            return ObjectId(task.uuid)
        except InvalidId:
            return None

    @staticmethod
    def get_timestamp(task: Task) -> datetime:
        return datetime.fromtimestamp(task.timestamp, tz=pytz.utc)

    @staticmethod
    def save_event(task_id: ObjectId, code: str, timestamp: datetime, **kwargs):
        event = {'code': code, 'timestamp': timestamp}
        event.update(kwargs)
        task_updates = {
            '$set': {'status': code, 'timestamp.{}'.format(code): timestamp},
            '$push': {'events': event}}
        Tasks().update_one({'_id': task_id}, task_updates)

        # update most recent task in schedule
        task = Tasks().find_one({'_id': task_id}, {'schedule._id': 1})
        schedule_id = task['schedule']['_id']
        schedule_update = {'$set': {'most_recent_task': {'_id': task_id, 'status': code, 'updated_at': timestamp}}}
        Schedules().update_one({'_id': schedule_id}, schedule_update)


class TaskSentEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Sent: {task_id}')

        self.save_event(task_id, TaskEvent.sent, self.get_timestamp(task))


class TaskReceivedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Received: {task_id}')

        self.save_event(task_id, TaskEvent.received, self.get_timestamp(task))


class TaskStartedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Started: {task_id}, hostname={task.worker.hostname}')

        self.save_event(task_id, TaskEvent.started, self.get_timestamp(task), hostname=task.worker.hostname)


class TaskSucceededEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)
        files = ast.literal_eval(task.result)

        logger.info(f'Task Succeeded: {task_id}, {task.timestamp}, {task.runtime}')

        self.save_event(task_id, TaskEvent.succeeded, self.get_timestamp(task),
                        hostname=task.worker.hostname, files=files)
        Tasks().update_one({'_id': task_id}, {'$set': {'files': files}})


class TaskFailedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Failed: {task_id}, {task.timestamp}')

        self.save_event(task_id, TaskEvent.failed, self.get_timestamp(task), hostname=task.worker.hostname,
                        exception=task.exception, traceback=task.traceback)


class TaskRetriedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info(f'Task Retried: {task_id}, {task.timestamp}')

        self.save_event(task_id, TaskEvent.retried, self.get_timestamp(task), hostname=task.worker.hostname,
                        exception=task.exception, traceback=task.traceback)
