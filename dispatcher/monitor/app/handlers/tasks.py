import ast
import logging
from typing import Optional

from bson.objectid import ObjectId, InvalidId
from celery.events.state import Task

from entities import TaskStatus
from mongo import Tasks
from handlers import BaseHandler

logger = logging.getLogger(__name__)


class BaseTaskEventHandler(BaseHandler):
    def __call__(self, event):
        self.state.event(event)

        task: Task = self.state.tasks.get(event['uuid'])
        logger.debug(task.info())
        return task

    @staticmethod
    def get_task_id(task: Task) -> Optional[ObjectId]:
        try:
            return ObjectId(task.uuid)
        except InvalidId:
            return None


class TaskSucceededEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)
        result = ast.literal_eval(task.result)

        logger.info('Task Succeeded: {}, {}, {}'.format(task_id, task.runtime, task.timestamp))

        update = {
            'status': TaskStatus.succeeded,
            'files': result
        }

        if task_id:
            Tasks().update_one({'_id': task_id}, {'$set': update})


class TaskFailedEventHandler(BaseTaskEventHandler):
    def __call__(self, event):
        task = super().__call__(event)
        task_id = self.get_task_id(task)
        exception = task.exception

        logger.info('Task Failed: {}, {}, {}'.format(task_id, exception, task.timestamp))

        update = {
            'status': TaskStatus.failed,
        }

        if task_id:
            Tasks().update_one({'_id': task_id}, {'$set': update})