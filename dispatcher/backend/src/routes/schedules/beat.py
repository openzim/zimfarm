from flask import jsonify

from mongo import Schedules

from .. import authenticate
from ..base import Route
from . import URLComponent


class ScheduleRoute(Route, URLComponent):
    rule = '/<string:schedule>/beat'
    name = 'beat'
    methods = ['GET']

    @authenticate
    def get(self, schedule: str, *args, **kwargs):
        query = self.get_schedule_query(schedule)

        beat = Schedules().find_one(query, {'beat': 1})
