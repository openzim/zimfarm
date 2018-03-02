from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, Response
from bson import ObjectId
from cerberus import Validator

from zimfarmworker import celery
from utils.mongo import Tasks
from utils.token import JWT
from utils.status import Task as TaskStatus
from . import errors


blueprint = Blueprint('task', __name__, url_prefix='/api/task')


@blueprint.route("/", methods=["GET"])
def tasks():
    token = request.headers.get('token')

    if token is None:
        projection = {
            'status': True,
            'created': True,
            'started': True,
            'finished': True,
            'offliner.name': True,
            'offliner.config.mwUrl': True
        }
    else:
        _ = JWT.decode(token)
        projection = {
            'status': True,
            'created': True,
            'started': True,
            'finished': True,
            'offliner': True,
        }

    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    sort = 1 if request.args.get('sort', -1) == 1 else -1

    cursor = Tasks().aggregate([
        {'$project': projection},
        {'$sort': {'created': sort}},
        {'$skip': offset},
        {'$limit': limit},
    ])
    tasks = [task for task in cursor]

    return jsonify({
        'meta': {
            'limit': limit,
            'offset': offset
        },
        'items': tasks
    })


@blueprint.route("/mwoffliner", methods=["POST"])
def enqueue_mwoffliner():
    """
    Enqueue a mwoffliner task
    :return:
    """
    def validate_task(config: dict):
        schema = {
            'mwUrl': {'type': 'string', 'required': True},
            'adminEmail': {'type': 'string', 'required': True},
            'verbose': {'type': 'boolean', 'required': False}
        }
        validator = Validator(schema, allow_unknown=True)

        if not validator.validate(config):
            raise errors.OfflinerConfigNotValid(validator.errors)

    def enqueue_task(config: dict):
        document = {
            'status': TaskStatus.PENDING.name,
            'created': datetime.utcnow(),
            'started': None,
            'finished': None,
            'offliner': {
                'name': "mwoffliner",
                'config': config
            },
            'steps': []
        }
        validator = Validator(Tasks.schema)
        if not validator.validate(document):
            raise errors.TaskDocumentNotValid(validator.errors)

        result = Tasks().insert_one(document)
        task_id = result.inserted_id

        celery.send_task('mwoffliner', task_id=str(task_id), kwargs={'offliner_config': config})

    # check token exist and is valid
    jwt = JWT.decode(request.headers.get('token'))
    if jwt is None:
        raise errors.BadRequest()

    # only admins can enqueue task
    if not jwt.is_admin:
        raise errors.NotEnoughPrivilege()

    request_data = request.get_json()
    if isinstance(request_data, list):
        for config in request_data:
            validate_task(config)
            enqueue_task(config)
    elif isinstance(request_data, dict):
        validate_task(request_data)
        enqueue_task(request_data)
    else:
        raise errors.BadRequest('A dict or list of task config is required.')
    return Response(status=202)


@blueprint.route("/<string:id>", methods=["GET", "PUT", "DELETE"])
def task(id: str):
    """

    PUT: update task data
    required:
    status: the key for task status enum
    """
    # check token exist and is valid
    jwt = JWT.decode(request.headers.get('token'))
    if jwt is None:
        raise errors.BadRequest()

    if id is None or id == '':
        raise errors.BadRequest('task id is required')

    if request.method == 'GET':
        task = Tasks().find_one({'_id': ObjectId(id)})
        return jsonify(task)
    elif request.method == 'PUT':
        request_data = request.get_json()
        update_set = {}
        current = Tasks().find_one({'_id': ObjectId(id)})

        # update task only when new task status is not older than old task status
        try:
            new_status = TaskStatus[request_data.get('status')]
            current_status = TaskStatus[current['status']]
            if new_status < current_status:
                return Response()
            else:
                update_set['status'] = new_status.name
        except KeyError:
            raise errors.BadRequest()

        # update start time when start time does not currently exist
        if current['started'] is None and new_status > TaskStatus.PENDING:
            update_set['started'] = datetime.utcnow()

        # update finished time when task is finished (successfully or error)
        # and start time exist, finished time does not exist
        if current['started'] is not None and current['finished'] is None and new_status >= TaskStatus.FINISHED:
            elapsed_second = request_data.get('elapsed_second')
            if elapsed_second is not None:
                update_set['finished'] = current['started'] + timedelta(seconds=elapsed_second)

        Tasks().update_one({'_id': ObjectId(id)}, {'$set': update_set})
        return Response()
    elif request.method == 'DELETE':
        # only admins can delete a task
        if not jwt.is_admin:
            raise errors.NotEnoughPrivilege()

        Tasks().delete_one({'_id': ObjectId(id)})
        return Response()