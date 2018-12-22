from flask import request, jsonify

from .. import authenticate

import abc

class Route:
    def __call__(self, *args, **kwargs):
        handlers = {
            'GET': self.get,
            'POST': self.post,
            'PATCH': self.patch,
            'DELETE': self.delete
        }
        handler = handlers[request.method]
        handler(*args, **kwargs)

    @abc.abstractmethod
    def get(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def post(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def patch(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def delete(self, *args, **kwargs):
        pass


class Schedule(Route):
    rule = '/<string:schedule>'
    name = 'schedule'
    methods = ['GET', 'POST', 'PATCH']

    def __init__(self):

        from datetime import datetime
        self.datetime = datetime.now()

    def get(self, *args, **kwargs):
        return jsonify({'datetime': self.datetime.isoformat()})

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