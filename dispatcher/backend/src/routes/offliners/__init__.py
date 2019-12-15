from routes import API_PATH
from routes.base import BaseBlueprint
from routes.offliners.offliner import offlinersRoute, offlinerRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__("offliner", __name__, url_prefix=f"{API_PATH}/offliners")

        self.register_route(offlinersRoute())
        self.register_route(offlinerRoute())
