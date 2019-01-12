import logging

from celery.events.state import Task

from . import BaseHandler

logger = logging.getLogger(__name__)


class BaseTaskEventHandler(BaseHandler):
    def __call__(self, event):
        self.state.event(event)
        logger.debug(event)
        print(event)

        task: Task = self.state.tasks.get(event['uuid'])
        logger.debug(task)
