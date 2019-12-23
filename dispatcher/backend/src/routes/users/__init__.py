from routes.base import BaseBlueprint

from routes import API_PATH
from routes.users.user import UsersRoute, UserRoute
from routes.users.keys import KeysRoute, KeyRoute
from routes.users.password import PasswordRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__("users", __name__, url_prefix=f"{API_PATH}/users")

        self.register_route(UsersRoute())
        self.register_route(UserRoute())
        self.register_route(KeysRoute())
        self.register_route(KeyRoute())
        self.register_route(PasswordRoute())
