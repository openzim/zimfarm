from celery.events.state import State, Worker, Task


class BaseHandler:
    def __init__(self):
        self.state: State = State()


class BaseTaskEventHandler(BaseHandler):
    def __call__(self, event, *args, **kwargs):
        self.state.event(event)
        print(event)
        # task: Task = self.state.tasks.get(event['task_id'])
        # worker: Worker = self.state.workers.get(event['hostname'])