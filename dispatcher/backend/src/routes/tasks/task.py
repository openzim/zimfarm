from flask import request, Response, jsonify
import pymongo
from bson.objectid import ObjectId, InvalidId

from errors.http import InvalidRequestJSON, TaskNotFound
from models import ScheduleService
from common.mongo import Tasks
from routes import authenticate
from routes.base import BaseRoute


class TasksRoute(BaseRoute):
    rule = '/'
    name = 'tasks'
    methods = ['POST', 'GET']

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

    @authenticate
    def get(self, *args, **kwargs):
        """Return a list of tasks"""

        # unpack url parameters
        skip = request.args.get('skip', default=0, type=int)
        limit = request.args.get('limit', default=100, type=int)
        skip = 0 if skip < 0 else skip
        limit = 100 if limit <= 0 else limit

        # get tasks from database
        filter = {'status': {'$nin': ['sent', 'received']}}
        projection = {'_id': 1, 'status': 1, 'schedule': 1}
        cursor = Tasks().find(filter, projection).sort('_id', pymongo.DESCENDING).skip(skip).limit(limit)
        tasks = [task for task in cursor]

        return jsonify({
            'meta': {
                'skip': skip,
                'limit': limit,
            },
            'items': tasks
        })


class TaskRoute(BaseRoute):
    rule = '/<string:task_id>'
    name = 'task'
    methods = ['GET']

    @authenticate
    def get(self, task_id: str, *args, **kwargs):
        try:
            task_id = ObjectId(task_id)
        except InvalidId:
            task_id = None

        task = Tasks().find_one({'_id': task_id})
        if task is None:
            raise TaskNotFound()
        else:
            return jsonify(task)
