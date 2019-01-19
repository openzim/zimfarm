from datetime import datetime
import pytz

from flask import request, Response

from routes import authenticate
from routes.base import BaseRoute
from errors.http import InvalidRequestJSON
from utils.celery import Celery
from mongo import Tasks, Schedules


class TasksRoute(BaseRoute):
    rule = '/'
    name = 'tasks'
    methods = ['POST']

    @authenticate
    def post(self, *args, **kwargs):
        """Create task from a schedule"""

        request_json = request.get_json()
        schedule_name = request_json.get('schedule_name')

        schedule = Schedules().find_one({'name': schedule_name}, {'config': 1})
        id = schedule.get('_id')
        config = schedule.get('config')

        if id and config:
            task_id = Tasks().insert_one({
                'schedule_id': id,
                'timestamp': {'created': datetime.utcnow().replace(tzinfo=pytz.utc)}
            }).inserted_id

            task_name = config.get('task_name')
            queue = config.get('queue')
            offliner = config.get('offliner')
            warehouse_path = config.get('warehouse_path')

            task_kwargs = {
                'offliner': offliner,
                'warehouse_path': warehouse_path
            }

            celery = Celery()
            celery.send_task(name=task_name, args=(), kwargs=task_kwargs, task_id=str(task_id), queue=queue)

            return Response()
        else:
            raise InvalidRequestJSON()
