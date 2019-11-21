from routes import API_PATH
from routes.base import BaseBlueprint
from routes.tasks.task import TasksRoute, TaskRoute, TaskCancelRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__("tasks", __name__, url_prefix=f"{API_PATH}/tasks")

        self.register_route(TasksRoute())
        self.register_route(TaskRoute())
        self.register_route(TaskCancelRoute())
