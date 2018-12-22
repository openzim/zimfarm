from http import HTTPStatus
from bson.objectid import ObjectId, InvalidId


from flask import request, jsonify, Response

from .. import authenticate
from mongo import Schedules


class Route:
    def __call__(self, *args, **kwargs):
        handlers = {
            'GET': self.get,
            'POST': self.post,
            'PATCH': self.patch,
            'DELETE': self.delete
        }
        handler = handlers[request.method]
        return handler(*args, **kwargs)

    def get(self, *args, **kwargs):
        return Response(status=HTTPStatus.METHOD_NOT_ALLOWED)

    def post(self, *args, **kwargs):
        return Response(status=HTTPStatus.METHOD_NOT_ALLOWED)

    def patch(self, *args, **kwargs):
        return Response(status=HTTPStatus.METHOD_NOT_ALLOWED)

    def delete(self, *args, **kwargs):
        return Response(status=HTTPStatus.METHOD_NOT_ALLOWED)


class Schedule(Route):
    rule = '/<string:schedule>'
    name = 'schedule'
    methods = ['GET', 'POST', 'PATCH']

    def __init__(self):

        from datetime import datetime
        self.datetime = datetime.now()

    @staticmethod
    def get_schedule_filter(schedule: str):
        try:
            schedule_id = ObjectId(schedule)
            return {'_id': schedule_id}
        except InvalidId:
            schedule_name = schedule
            return {'name': schedule_name}

    @authenticate
    def get(self, schedule: str, *args, **kwargs):
        filter = self.get_schedule_filter(schedule)
        schedule = Schedules().find_one(filter)
        return jsonify(schedule)

    def post(self, *args, **kwargs):
        pass

    def patch(self):
        pass



# @authenticate
# def update(token: AccessControl, schedule_id: ObjectId, schedule_name: str):
#     """Update fields of schedule"""
#
#     schedules = Schedules()
#     schedules.find_one()
#
#
# def schedule_filter(f):
#     @wraps(f)
#     def wrapper(*args, **kwargs):
#         schedule_id_name = kwargs.pop('schedule_id_name')
#
#         try:
#             schedule_id = ObjectId(schedule_id_name)
#             filter = {'_id': schedule_id}
#         except InvalidId:
#             schedule_name = schedule_id_name
#             filter = {'name': schedule_name}
#
#         kwargs['filter'] = filter
#         return f(*args, **kwargs)
#     return wrapper