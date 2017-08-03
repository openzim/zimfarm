from datetime import datetime

import pymongo.errors
from flask import Blueprint, request, jsonify, Response

from app import celery
from mongo import TasksCollection
from utils.token import UserJWT, MWOfflinerTaskJWT
from .error import exception


blueprint = Blueprint('task', __name__, url_prefix='/task')


@blueprint.route("/mwoffliner", methods=["POST"])
def enqueue_mwoffliner():
    token = UserJWT.from_request_header(request)

    # only admins can enqueue task
    if not token.is_admin:
        raise exception.NotEnoughPrivilege()

    config = request.get_json()
    mwoffliner = config.get('mwoffliner')
    if mwoffliner is None:
        raise exception.InvalidRequest()
    if mwoffliner.get('mwUrl') is None or mwoffliner.get('adminEmail') is None:
        raise exception.InvalidRequest()

    task_name = 'mwoffliner'
    celery_task = celery.send_task(task_name, kwargs={
        'token': MWOfflinerTaskJWT.new(),
        'config': config
    })

    collection = TasksCollection()
    collection.insert_one({
        '_id': celery_task.id,
        'celery_task_name': task_name,
        'status': 'PENDING',
        'time_stamp': {'created': datetime.utcnow(), 'started': None, 'ended': None},
        'options': config,
        'stages': []
    })

    return Response(status=202)


@blueprint.route("/", methods=["GET"])
def tasks():
    _ = UserJWT.from_request_header(request)

    limit = request.args.get('limit', 10)
    offset = request.args.get('limit', 0)

    cursor = TasksCollection().aggregate([
        {'$project': {
            'id': '$_id',
            '_id': False,
            'status': True,
            'time_stamp.created': True
        }},
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
        json = request.get_json()

        status = json.get('status')
        stages = json.get('stages')

        if status is None or stages is None:
            raise exception.InvalidRequest()

        try:
            result = TasksCollection().update_one({'_id': id}, {'$set': {'status': status, 'stages': stages}})
            if result.modified_count != 1:
                raise exception.TaskDoesNotExist()
        except pymongo.errors.WriteError as e:
            raise exception.InvalidRequest()

        return Response(status=200)
    elif request.method == 'DELETE':
        TasksCollection().delete_one({'_id': id})
        return Response(status=200)
