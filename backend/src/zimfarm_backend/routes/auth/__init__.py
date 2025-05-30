# class Blueprint(flask.Blueprint):
#     def __init__(self):
#         super().__init__("auth", __name__, url_prefix=f"{API_PATH}/auth")
# methods=["POST"])
#         self.add_url_rule("/oauth2", "oauth2", OAuth2(), methods=["POST"])
#
from zimfarm_backend.routes.auth.logic import router

__all__ = ["router"]
