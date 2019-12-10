from routes import API_PATH
from routes.base import BaseBlueprint
from routes.workers.worker import WorkersRoute, WorkerCheckinRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__("workers", __name__, url_prefix=f"{API_PATH}/workers")

        self.register_route(WorkersRoute())
        self.register_route(WorkerCheckinRoute())
