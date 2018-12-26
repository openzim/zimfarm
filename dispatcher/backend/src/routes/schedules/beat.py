import trafaret
from flask import jsonify, request, Response

from errors.http import ScheduleNotFound, InvalidRequestJSON
from mongo import Schedules
from .base import URLComponent
from .validators import CrontabValidator
from .. import authenticate
from ..base import BaseRoute


class BeatRoute(BaseRoute, URLComponent):
    rule = '/<string:schedule>/beat'
    name = 'beat'
    methods = ['GET', 'PATCH']

    @authenticate
    def get(self, schedule: str, *args, **kwargs):
        """Get schedule beat"""

        query = self.get_schedule_query(schedule)
        schedule = Schedules().find_one(query, {'beat': 1})

        if schedule is None:
            raise ScheduleNotFound()
        else:
            beat = schedule.get('beat', {})
            return jsonify(beat)

    @authenticate
    def patch(self, schedule: str, *args, **kwargs):
        """Update schedule beat:

        Crontab beat:
        - minute
        - hour
        - day_of_week
        - day_of_month
        - month_of_year
        """

        try:
            query = self.get_schedule_query(schedule)
            request_json = request.get_json()
            if request_json is None:
                raise InvalidRequestJSON()

            beat_type = request_json.get('type')
            config = request_json.get('config')

            if beat_type == 'crontab':
                config = CrontabValidator().check(config)
                beat = {'type': beat_type, 'config': config}
                matched_count = Schedules().update_one(query, {'$set': {'beat': beat}}).matched_count
            else:
                raise InvalidRequestJSON('Invalid beat type')

            if matched_count:
                return Response()
            else:
                raise ScheduleNotFound()
        except trafaret.DataError as e:
            raise InvalidRequestJSON(str(e.error))
