import flask

from . import schedule


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__('schedules', __name__, url_prefix='/api/schedules')

        self.add_url_rule('/', 'list_schedules', schedule.list, methods=['GET'])
