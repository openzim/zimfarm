from datetime import datetime
import pytz

from flask import request

from routes import authenticate
from routes.base import BaseRoute
from errors.http import InvalidRequestJSON
from utils.celery import Celery
from mongo import Tasks, Schedules


@authenticate
class TasksRoute(BaseRoute):
    rule = '/'
    name = 'tasks'
    methods = ['POST']

    @authenticate
    def post(self, *args, **kwargs):
        """Create task from a schedule"""

        request_json = request.get_json()
        schedule_name = request_json.get('schedule_name')

        schedule = Schedules().find_one({'name': schedule_name})

        if schedule:
            task_id = Tasks().insert_one({
                'schedule_id': schedule['_id'],
                'debug': True,
                'timestamp': {
                    'created': datetime.utcnow().replace(tzinfo=pytz.utc)
                }
            }).inserted_id

            celery = Celery
            celery.send_task()
        else:
            raise InvalidRequestJSON()
