import flask

from .schedule import ScheduleRoute, SchedulesRoute


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__('schedules', __name__, url_prefix='/api/schedules')

        self.add_url_rule(SchedulesRoute.rule, SchedulesRoute.name, SchedulesRoute(), methods=SchedulesRoute.methods)
        self.add_url_rule(ScheduleRoute.rule, ScheduleRoute.name, ScheduleRoute(), methods=ScheduleRoute.methods)
