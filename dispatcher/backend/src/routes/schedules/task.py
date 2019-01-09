import trafaret
from flask import jsonify, request, Response

from errors.http import ScheduleNotFound, InvalidRequestJSON
from mongo import Schedules
from .base import URLComponent
from .. import authenticate
from ..base import BaseRoute
from .validators import MWOfflinerConfigValidator


class TaskRoute(BaseRoute, URLComponent):
    rule = '/<string:schedule>/task'
    name = 'task'
    methods = ['GET']

    @authenticate
    def get(self, schedule: str):
        """Get schedule task config"""

        query = self.get_schedule_query(schedule)
        schedule = Schedules().find_one(query, {'task': 1})

        if schedule is None:
            raise ScheduleNotFound()
        else:
            task = schedule.get('task', {})
            return jsonify(task)

    # @authenticate
    # def patch(self, schedule: str, *args, **kwargs):
    #     """Update schedule task config"""
    #
    #     query = self.get_schedule_query(schedule)
    #     request_json = request.get_json()
    #     if request_json is None:
    #         raise InvalidRequestJSON()
    #
    #     image_name = request_json.get('image_name')
    #     config = request_json.get('config')
    #
    #     if image_name == 'openzim/mwoffliner':
    #         try:
    #             config = MWOfflinerConfigValidator().check(config)
    #         except trafaret.DataError as e:
    #             raise InvalidRequestJSON(str(e.error))
    #
    #         task = {
    #             'image_name': 'openzim/mwoffliner',
    #             'image_tag': 'latest',
    #             'warehouse_path': '/wikipedia',
    #             'config': config
    #         }
    #         matched_count = Schedules().update_one(query, {'$set': {'offliner': offliner}}).matched_count
    #     else:
    #         raise InvalidRequestJSON('Invalid beat type')
    #
    #     if matched_count:
    #         return Response()
    #     else:
    #         raise ScheduleNotFound()
