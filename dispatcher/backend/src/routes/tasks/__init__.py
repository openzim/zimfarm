from routes.base import BaseBlueprint
from routes.tasks.task import TasksRoute, TaskRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__('tasks', __name__, url_prefix='/api/tasks')

        self.register_route(TasksRoute())
        self.register_route(TaskRoute())
