import trafaret
from flask import jsonify, request, Response

from errors.http import ScheduleNotFound, InvalidRequestJSON
from mongo import Schedules
from .base import URLComponent
from .validators import CrontabValidator
from .. import authenticate
from ..base import Route


class BeatRoute(Route, URLComponent):
    rule = '/<string:schedule>/beat'
    name = 'beat'
    methods = ['GET', 'PATCH']

    @authenticate
    def get(self, schedule: str, *args, **kwargs):
        query = self.get_schedule_query(schedule)
        schedule = Schedules().find_one(query, {'beat': 1})

        if schedule is None:
            raise ScheduleNotFound()
        else:
            beat = schedule.get('beat', {})
            return jsonify(beat)

    @authenticate
    def patch(self, schedule: str, *args, **kwargs):
        """
        Update schedule beat:
        - minute
        - hour
        - day_of_week
        - day_of_month
        - month_of_year
        """

        try:
            query = self.get_schedule_query(schedule)
            request_json = request.get_json()
            beat_type = request_json.get('type')
            config = request_json.get('config')

            if beat_type == 'crontab':
                config = CrontabValidator().check(config)
                beat = {'type': beat_type, 'config': config}
                modified_count = Schedules().update_one(query, {'$set': {'beat': beat}}).modified_count
            else:
                raise InvalidRequestJSON('Invalid beat type')

            if modified_count:
                return Response()
            else:
                raise ScheduleNotFound()
        except trafaret.DataError as e:
            raise InvalidRequestJSON(str(e.error))
