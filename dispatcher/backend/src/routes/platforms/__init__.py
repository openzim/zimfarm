from routes import API_PATH
from routes.base import BaseBlueprint
from routes.platforms.platform import platformsRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__("platforms", __name__, url_prefix=f"{API_PATH}/platforms")

        self.register_route(platformsRoute())
