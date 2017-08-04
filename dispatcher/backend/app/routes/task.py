from datetime import datetime

import pymongo.errors
from flask import Blueprint, request, jsonify, Response

from app import celery
from mongo import TasksCollection
from utils.token import UserJWT, TaskJWT
from utils.status import TaskStatus
from .error import exception


blueprint = Blueprint('task', __name__, url_prefix='/task')


@blueprint.route("/mwoffliner", methods=["POST"])
def enqueue_mwoffliner():
    token = UserJWT.from_request_header(request)

    # only admins can enqueue task
    if not token.is_admin:
        raise exception.NotEnoughPrivilege()

    def check_task(config: dict):
        # check config is a dict
        if not isinstance(config, dict):
            raise exception.InvalidRequest()

        # check config has mandatory data
        if config.get('mwUrl') is None or config.get('adminEmail') is None:
            raise exception.InvalidRequest()

    def enqueue_task(config: dict):
        task_name = 'mwoffliner'

        celery_task = celery.send_task(task_name, kwargs={
            'token': TaskJWT.new(task_name),
            'config': config
        })

        TasksCollection().insert_one({
            '_id': celery_task.id,
            'celery_task_name': task_name,
            'status': 'PENDING',
            'time_stamp': {'created': datetime.utcnow(), 'started': None, 'ended': None},
            'options': config,
            'steps': []
        })

    task_configs = request.get_json()
    if not isinstance(task_configs, list):
        raise exception.InvalidRequest()
    for task_config in task_configs:
        check_task(task_config)
    for task_config in task_configs:
        enqueue_task(task_config)
    return Response(status=202)


@blueprint.route("", methods=["GET"])
def tasks():
    _ = UserJWT.from_request_header(request)

    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort_desc = request.args.get('sort', 'desc') != 'asc'

    cursor = TasksCollection().aggregate([
        {'$project': {
            'id': '$_id',
            '_id': False,
            'celery_task_name': True,
            'status': True,
            'time_stamp.created': True
        }},
        {'$sort': {'time_stamp.created': -1 if sort_desc else 1}},
        {'$skip': offset},
        {'$limit': limit},
    ])
    tasks = [task for task in cursor]

    return jsonify({
        'limit': limit,
        'offset': offset,
        'tasks': tasks
    })


@blueprint.route("/<string:id>", methods=["GET", "PUT", "DELETE"])
def task(id):
    if request.method == 'GET':
        _ = UserJWT.from_request_header(request)

        task = TasksCollection().find_one({'_id': id})

        if task is None:
            raise exception.TaskDoesNotExist()

        return jsonify(task)
    elif request.method == 'PUT':
        _ = TaskJWT.from_request_header(request)
        json = request.get_json()

        status_name = json.get('status')
        steps = json.get('steps')
        time_stamp = json.get('time_stamp')
        file_name = json.get('file_name')

        if status_name is None or steps is None or time_stamp is None:
            raise exception.InvalidRequest()

        try:
            new_status = TaskStatus[status_name]
            current_status = TaskStatus[TasksCollection().find_one({'_id': id}, {'status': 1})['status']]
            if current_status.value > new_status.value:
                return

            result = TasksCollection().update_one({'_id': id}, {'$set': {
                'status': new_status.name,
                'steps': steps,
                'file_name': file_name,
                'time_stamp.started': time_stamp['started'],
                'time_stamp.ended': time_stamp['ended']
            }})
            if result.modified_count != 1:
                raise exception.TaskDoesNotExist()
        except pymongo.errors.WriteError as e:
            raise exception.InvalidRequest()

        return Response(status=200)
    elif request.method == 'DELETE':
        TasksCollection().delete_one({'_id': id})
        return Response(status=200)
