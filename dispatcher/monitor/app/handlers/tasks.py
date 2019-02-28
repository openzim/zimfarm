import ast
import logging
from datetime import datetime
from typing import Optional

import pytz
from bson.objectid import ObjectId, InvalidId
from celery.events.state import Task

from entities import TaskEvent
from handlers import BaseHandler
from common.mongo import Tasks

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
        updates = {
            '$set': {'timestamp.{}'.format(code): timestamp},
            '$push': {'events': event}}
        Tasks().update_one({'_id': task_id}, updates)


class TaskSentEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info('Task Sent: {id}'.format(id=task_id))

        self.save_event(task_id, TaskEvent.sent, self.get_timestamp(task))


class TaskReceivedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info('Task Received: {id}'.format(id=task_id))

        self.save_event(task_id, TaskEvent.received, self.get_timestamp(task))


class TaskStartedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info('Task Started: {id}, hostname={hostname}'.format(id=task_id, hostname=task.worker.hostname))

        self.save_event(task_id, TaskEvent.started, self.get_timestamp(task))


class TaskSucceededEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)
        files = ast.literal_eval(task.result)

        logger.info('Task Succeeded: {}, {}, {}'.format(task_id, task.timestamp, task.runtime))

        self.save_event(task_id, TaskEvent.succeeded, self.get_timestamp(task))
        Tasks().update_one({'_id': task_id}, {'$set': {'files': files}})


class TaskFailedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info('Task Failed: {}, {}, {}'.format(task_id, task.timestamp, task.exception))

        self.save_event(task_id, TaskEvent.failed, self.get_timestamp(task),
                        exception=task.exception, traceback=task.traceback)


class TaskRetriedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)

        logger.info('Task Retried: {}, {}, {}'.format(task_id, task.timestamp, task.exception))

        self.save_event(task_id, TaskEvent.retried, self.get_timestamp(task),
                        exception=task.exception, traceback=task.traceback)
