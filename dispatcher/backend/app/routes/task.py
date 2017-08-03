from datetime import datetime

import pymongo
from flask import Blueprint, request, jsonify, Response

from app import celery
from mongo import TasksCollection
from utils.token import UserJWT, MWOfflinerTaskJWT
from .error import exception

blueprint = Blueprint('task', __name__, url_prefix='/task')


@blueprint.route("/enqueue/generic", methods=["POST"])
def enqueue_zimfarm_generic():
    token = UserJWT.from_request_header(request)

    if not token.is_admin:
        raise exception.NotEnoughPrivilege()

    json = request.get_json()
    image_name = json.get('image_name')
    script = json.get('script')

    if image_name is None or script is None:
        raise exception.InvalidRequest()

    task_name = 'generic'
    kwargs = {
        'image_name': image_name,
        'script': script,
    }
    celery_task = celery.send_task(task_name, kwargs=kwargs)
    # database_task = database.task.add(celery_task.id, task_name, GenericTaskStatus.PENDING, image_name, script)
    return Response(status=202)


@blueprint.route("/enqueue/mwoffliner", methods=["POST"])
def enqueue_mwoffliner():
    token = UserJWT.from_request_header(request)

    # only admins can enqueue task
    if not token.is_admin:
        raise exception.NotEnoughPrivilege()

    json = request.get_json()
    if json.get('mwUrl') is None or json.get('adminEmail') is None:
        raise exception.InvalidRequest()

    task_name = 'mwoffliner'
    celery_task = celery.send_task(task_name, kwargs={
        'token': MWOfflinerTaskJWT.new(),
        'params': json
    })

    collection = TasksCollection()
    collection.insert_one({
        '_id': celery_task.id,
        'celery_task_name': task_name,
        'status': 'PENDING',
        'time_stamp': {'created': datetime.utcnow(), 'started': None, 'ended': None},
        'options': {'mwoffliner': json},
        'stages': []
    })

    return Response(status=202)


@blueprint.route("/", methods=["GET"])
def tasks():
    _ = UserJWT.from_request_header(request)

    limit = request.args.get('limit', 10)
    offset = request.args.get('limit', 0)

    cursor = TasksCollection().find(skip=offset, limit=limit).sort('time_stamp.created', pymongo.DESCENDING)
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

        TasksCollection().update_one({'_id': id}, {'$set': {'status': status, 'stages': stages}})

        return Response(status=200)
    elif request.method == 'DELETE':
        TasksCollection().delete_one({'_id': id})
        return Response(status=200)
