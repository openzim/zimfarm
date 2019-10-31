import flask

from . import worker


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__("workers", __name__, url_prefix="/workers")

        self.add_url_rule("/", "list_workers", worker.list, methods=["GET"])
