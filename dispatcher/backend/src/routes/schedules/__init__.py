import flask
from bson.objectid import ObjectId, InvalidId

from .schedule import ScheduleRoute, SchedulesRoute


class Blueprint(flask.Blueprint):
    def __init__(self):
        super().__init__('schedules', __name__, url_prefix='/api/schedules')

        self.add_url_rule(SchedulesRoute.rule, SchedulesRoute.name, SchedulesRoute(), methods=SchedulesRoute.methods)
        self.add_url_rule(ScheduleRoute.rule, ScheduleRoute.name, ScheduleRoute(), methods=ScheduleRoute.methods)


class URLComponent:
    @staticmethod
    def get_schedule_query(schedule_id_or_name: str):
        try:
            schedule_id = ObjectId(schedule_id_or_name)
            return {'_id': schedule_id}
        except InvalidId:
            schedule_name = schedule_id_or_name
            return {'name': schedule_name}