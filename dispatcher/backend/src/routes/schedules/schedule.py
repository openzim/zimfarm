from http import HTTPStatus

import trafaret
from bson.objectid import ObjectId, InvalidId
from flask import request, jsonify, Response

from models.schedule import ScheduleCategory
from mongo import Schedules
from .. import authenticate
from ..base import Route

from errors.http import InvalidRequestJSON, ScheduleNotFound


class ScheduleRoute(Route):
    rule = '/<string:schedule>'
    name = 'schedule'
    methods = ['GET', 'PATCH']

    @staticmethod
    def get_schedule_query(schedule: str):
        try:
            schedule_id = ObjectId(schedule)
            return {'_id': schedule_id}
        except InvalidId:
            schedule_name = schedule
            return {'name': schedule_name}

    @authenticate
    def get(self, schedule: str, *args, **kwargs):
        """Get schedule object."""

        query = self.get_schedule_query(schedule)
        schedule = Schedules().find_one(query)
        if schedule is None:
            raise ScheduleNotFound()
        else:
            return jsonify(schedule)

    @authenticate
    def patch(self, schedule: str, *args, **kwargs):
        """
        Update properties of a schedule, including:
        - name
        - language
        - category
        - enabled
        """

        try:
            name = trafaret.String(allow_blank=False)
            language = trafaret.String(allow_blank=False)
            category = trafaret.Enum(*ScheduleCategory.all_values())
            validator = trafaret.Dict(
                trafaret.Key('name', optional=True, trafaret=name),
                trafaret.Key('language', optional=True, trafaret=language),
                trafaret.Key('category', optional=True, trafaret=category))

            update = request.get_json()
            update = validator.check(update)

            query = self.get_schedule_query(schedule)
            matched_count = Schedules().update_one(query, {'$set': update}).matched_count

            if matched_count:
                return Response()
            else:
                raise ScheduleNotFound()
        except trafaret.DataError as e:
            raise InvalidRequestJSON(str(e.error))
