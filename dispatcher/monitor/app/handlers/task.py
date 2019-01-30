import logging
import ast

from bson.objectid import ObjectId, InvalidId
from celery.events.state import Task

from mongo import Tasks
from . import BaseHandler
from entities import TaskStatus
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

        logger.info('Task Succeeded: {}'.format(task_id))

        if task_id:
            Tasks().update_one({'_id': task_id},
                               {'$set': {'status': TaskStatus.succeeded, 'files': result}})
