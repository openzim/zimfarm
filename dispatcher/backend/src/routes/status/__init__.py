from routes import API_PATH
from routes.base import BaseBlueprint
from routes.status.status import StatusMonitorRoute  # , StatusFooRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__("status", __name__, url_prefix=f"{API_PATH}/status")

        self.register_route(StatusMonitorRoute())
