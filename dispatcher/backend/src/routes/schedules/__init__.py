import flask

from . import schedules
from .schedule import Schedule


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__('schedules', __name__, url_prefix='/api/schedules')

        self.add_url_rule('/', 'list_schedules', schedules.list, methods=['GET'])

        # self.add_url_rule('/<string:schedule_id_name>', 'update_schedule', schedules.update, methods=['PATCH'])
        self.add_url_rule(Schedule.rule, Schedule.name, Schedule(), methods=Schedule.methods)
