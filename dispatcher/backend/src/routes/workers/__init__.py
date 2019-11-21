import flask

from routes import API_PATH
from . import worker


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__("workers", __name__, url_prefix=f"{API_PATH}/workers")

        self.add_url_rule("/", "list_workers", worker.list_workers, methods=["GET"])
