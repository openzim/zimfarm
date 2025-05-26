from routes import API_PATH
from routes.base import BaseBlueprint
from routes.users.keys import KeyRoute, KeysRoute
from routes.users.password import PasswordRoute
from routes.users.user import UserRoute, UsersRoute


class Blueprint(BaseBlueprint):
    def __init__(self):
        super().__init__("users", __name__, url_prefix=f"{API_PATH}/users")

        self.register_route(UsersRoute())
        self.register_route(UserRoute())
        self.register_route(KeysRoute())
        self.register_route(KeyRoute())
        self.register_route(PasswordRoute())
