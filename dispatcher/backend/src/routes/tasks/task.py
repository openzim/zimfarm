import pymongo
import trafaret as t
from bson.objectid import ObjectId, InvalidId
from flask import request, Response, jsonify

from common.entities import TaskStatus
from common.mongo import RequestedTasks, Tasks, Schedules
from errors.http import InvalidRequestJSON, TaskNotFound
from routes import authenticate
from routes.base import BaseRoute
from routes.errors import NotFound
from utils.celery import Celery
from common.validators import ObjectIdValidator


class TasksRoute(BaseRoute):
    rule = '/'
    name = 'tasks'
    methods = ['GET']

    @authenticate
    def get(self, *args, **kwargs):
        """Return a list of tasks"""

        # validate query parameter
        request_args = request.args.to_dict()
        request_args['status'] = request.args.getlist('status')
        validator = t.Dict({
            t.Key('skip', default=0): t.Int(gte=0),
            t.Key('limit', default=100): t.Int(gt=0, lte=200),
            t.Key('status', optional=True): t.List(t.Enum(*TaskStatus.all())),
            t.Key('schedule_id', optional=True): ObjectIdValidator
        })
        request_args = validator.check(request_args)

        # unpack query parameter
        skip, limit = request_args['skip'], request_args['limit']
        statuses = request_args.get('status')
        schedule_id = request_args.get('schedule_id')

        # get tasks from database
        if statuses:
            filter = {'status': {'$in': statuses}}
        else:
            filter = {'status': {'$nin': ['sent', 'received']}}
        if schedule_id:
            filter['schedule._id'] = schedule_id
        projection = {'_id': 1, 'status': 1, 'schedule': 1}
        cursor = Tasks()\
            .find(filter, projection)\
            .sort('_id', pymongo.DESCENDING)\
            .skip(skip)\
            .limit(limit)
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
    methods = ['GET', 'POST']

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

    @authenticate
    def post(self, task_id: str, *args, **kwargs):
        """ create a task from a requested_task_id """
        # TODO
        try:
            task_id = ObjectId(task_id)
        except InvalidId:
            task_id = None

        task = RequestedTasks().find_one({'_id': task_id})
        if task is None:
            raise TaskNotFound()

        schedule = Schedules().find_one({"name": task["schedule_name"]}, {"config": 1})
        config = schedule.get("config")

        if not config:
            raise TaskNotFound()

        requested_task_id = (
            RequestedTasks()
            .insert_one(
                {"schedule": {"_id": schedule["_id"], "name": schedule_name}}
            )
            .inserted_id
        )

        task_name = config.get("task_name")
        queue = config.get("queue")

        task_kwargs = {
            "flags": config.get("flags"),
            "image": config.get("image"),
            "queue": queue,
            "warehouse_path": config.get("warehouse_path"),
        }

        return jsonify(task)


class TaskCancelRoute(BaseRoute):
    rule = '/<string:task_id>/cancel'
    name = 'task_cancel'
    methods = ['POST']

    @authenticate
    def post(self, task_id: str, *args, **kwargs):

        try:
            task_id = ObjectId(task_id)
        except InvalidId:
            task_id = None

        task = Tasks().find_one(
            {'$or': [{'status': {'$exists': False}, '_id': task_id},
                     {'status': {'$in': TaskStatus.incomplete()}, '_id': task_id}]})
        if task is None:
            raise TaskNotFound()

        celery = Celery()
        celery.control.revoke(str(task_id), terminate=True)

        return Response()
