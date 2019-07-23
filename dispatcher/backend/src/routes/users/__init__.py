import flask


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__('users', __name__, url_prefix='/api/users')
