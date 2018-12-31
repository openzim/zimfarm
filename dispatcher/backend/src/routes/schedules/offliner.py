import trafaret
from flask import jsonify, request, Response

from errors.http import ScheduleNotFound, InvalidRequestJSON
from mongo import Schedules
from .base import URLComponent
from .. import authenticate
from ..base import BaseRoute
from .validators import MWOfflinerConfigValidator


class OfflinerRoute(BaseRoute, URLComponent):
    rule = '/<string:schedule>/offliner'
    name = 'offliner'
    methods = ['GET', 'PATCH']

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
        """Update schedule offliner"""

        query = self.get_schedule_query(schedule)
        request_json = request.get_json()
        if request_json is None:
            raise InvalidRequestJSON()

        offliner_name = request_json.get('name')
        config = request_json.get('config')

        if offliner_name == 'mwoffliner':
            try:
                config = MWOfflinerConfigValidator().check(config)
            except trafaret.DataError as e:
                raise InvalidRequestJSON(str(e.error))

            offliner = {'name': offliner_name, 'config': config}
            matched_count = Schedules().update_one(query, {'$set': {'offliner': offliner}}).matched_count
        else:
            raise InvalidRequestJSON('Invalid beat type')

        if matched_count:
            return Response()
        else:
            raise ScheduleNotFound()
