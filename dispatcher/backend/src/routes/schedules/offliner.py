from flask import jsonify, request, Response

from errors.http import ScheduleNotFound
from mongo import Schedules
from .base import URLComponent
from .. import authenticate
from ..base import BaseRoute


class OfflinerRoute(BaseRoute, URLComponent):
    route = '/<string:schedule>/offliner'
    name = 'offliner'
    methods = ['GET']

    @authenticate
    def get(self, schedule: str):
        """Get schedule offliner"""

        query = self.get_schedule_query(schedule)
        schedule = Schedules().find_one(query, {'offliner': 1})

        if schedule is None:
            raise ScheduleNotFound()
        else:
            beat = schedule.get('offliner', {})
            return jsonify(beat)

    @authenticate
    def patch(self, schedule: str, *args, **kwargs):
        pass
