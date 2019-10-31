from routes.base import BaseBlueprint
from routes.tags.tag import tagsRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__("tags", __name__, url_prefix="/tags")

        self.register_route(tagsRoute())
