from flask import jsonify

from mongo import Schedules

from .. import authenticate
from ..base import Route
from .base import URLComponent

from errors.http import ScheduleNotFound


class ScheduleRoute(Route, URLComponent):
    rule = '/<string:schedule>/beat'
    name = 'beat'
    methods = ['GET']

    @authenticate
    def get(self, schedule: str, *args, **kwargs):
        query = self.get_schedule_query(schedule)

        schedule = Schedules().find_one(query, {'beat': 1})

        if schedule is None:
            raise ScheduleNotFound()
        else:
            beat = schedule.get('beat', {})
            return jsonify(beat)
