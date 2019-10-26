from routes.base import BaseBlueprint
from routes.requested_tasks.requested_task import (
    RequestedTasksRoute,
    RequestedTaskRoute,
    RequestedTaskDeleteRoute,
)


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__("requested-tasks", __name__, url_prefix="/api/requested-tasks")

        self.register_route(RequestedTasksRoute())
        self.register_route(RequestedTaskRoute())
        self.register_route(RequestedTaskDeleteRoute())
