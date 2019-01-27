from flask import request, Response

from errors.http import InvalidRequestJSON
from models import ScheduleService
from routes import authenticate
from routes.base import BaseRoute


class TasksRoute(BaseRoute):
    rule = '/'
    name = 'tasks'
    methods = ['POST']

    @authenticate
    def post(self, *args, **kwargs):
        """Create task from a schedule"""

        request_json = request.get_json()
        if not request_json:
            raise InvalidRequestJSON()

        schedule_names = request_json.get('schedule_names', [])
        for schedule_name in schedule_names:
            ScheduleService.send_task(schedule_name)

        return Response()
