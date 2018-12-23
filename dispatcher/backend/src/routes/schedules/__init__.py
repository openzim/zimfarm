import flask

from . import schedules
from .scheduleroute import ScheduleRoute


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__('schedules', __name__, url_prefix='/api/schedules')

        self.add_url_rule('/', 'list_schedules', schedules.list, methods=['GET'])

        self.add_url_rule(ScheduleRoute.rule, ScheduleRoute.name, ScheduleRoute(), methods=ScheduleRoute.methods)
