import flask

from routes import API_PATH
from . import user, keys, password


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__("users", __name__, url_prefix=f"{API_PATH}/users")

        self.add_url_rule("/", "list_users", user.list, methods=["GET"])
        self.add_url_rule("/", "create_user", user.create, methods=["POST"])

        self.add_url_rule("/<string:username>", "get_user", user.get, methods=["GET"])
        self.add_url_rule(
            "/<string:username>", "delete_user", user.delete, methods=["DELETE"]
        )

        self.add_url_rule(
            "/<string:username>/keys", "list_ssh_keys", keys.list, methods=["GET"]
        )
        self.add_url_rule(
            "/<string:username>/keys", "add_ssh_keys", keys.add, methods=["POST"]
        )
        self.add_url_rule(
            "/<string:username>/keys/<string:fingerprint>",
            "delete_ssh_keys",
            keys.delete,
            methods=["DELETE"],
        )

        self.add_url_rule(
            "/<string:username>/password",
            "update_user_password",
            password.update,
            methods=["PATCH"],
        )
