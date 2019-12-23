from routes import API_PATH
from routes.base import BaseBlueprint
from routes.requested_tasks.requested_task import (
    RequestedTasksRoute,
    RequestedTaskRoute,
    RequestedTasksForWorkers,
)


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__(
            "requested-tasks", __name__, url_prefix=f"{API_PATH}/requested-tasks"
        )

        self.register_route(RequestedTasksRoute())
        self.register_route(RequestedTasksForWorkers())
        self.register_route(RequestedTaskRoute())
