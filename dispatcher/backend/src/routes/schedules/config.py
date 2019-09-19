from bson.objectid import ObjectId, InvalidId
from flask import request
from flask.views import MethodView
from marshmallow import ValidationError

from common.mongo import Schedules
from common.schemas import ScheduleConfigSchema
from errors.http import InvalidRequestJSON
from errors.http import ScheduleNotFound
from .. import authenticate


class ConfigRoute(MethodView):
    rule = '/<string:schedule_id>/config/'
    name = 'schedule_config'

    @authenticate
    def patch(self, schedule_id: str):
        try:
            request_json = ScheduleConfigSchema().load(request.json, partial=True)
        except ValidationError as e:
            print(request.json)
            raise InvalidRequestJSON()

        try:
            schedule_id = ObjectId(schedule_id)
        except InvalidId:
            raise ScheduleNotFound()

        schedule = Schedules().find_one({'_id': schedule_id}, {'config': 1})
        if not schedule:
            raise ScheduleNotFound()

        config = schedule.get('config', {})
        config.update(request.json)

        try:
            config = ScheduleConfigSchema().load(config)
            config = ScheduleConfigSchema().dump(config)
        except ValidationError as e:
            raise InvalidRequestJSON(e.messages)

        Schedules().update_one({'_id': schedule_id}, {'config': config})
        return ''
