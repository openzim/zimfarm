from celery.events.state import Task

from . import BaseHandler


class BaseTaskEventHandler(BaseHandler):
    def __call__(self, event):
        self.state.event(event)
        print(event)

        task: Task = self.state.tasks.get(event['uuid'])
        print(task)
