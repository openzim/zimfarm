import trafaret
from flask import request, jsonify, Response

from errors.http import InvalidRequestJSON, ScheduleNotFound
from models.schedule import ScheduleCategory
from mongo import Schedules
from .. import authenticate
from routes.base import BaseRoute
from .base import URLComponent


class OfflinerFlagsRoute(BaseRoute, URLComponent):
    rule = '/<string:schedule>/config/offliner/flags'
    name = 'schedule_config_offliner_flags'
    methods = ['PATCH']

    @authenticate
    def patch(self, schedule: str):
        query = self.get_schedule_query(schedule)
        request_json = request.get_json()
        if request_json is None:
            raise InvalidRequestJSON()