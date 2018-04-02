from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, Response
from bson import ObjectId
from cerberus import Validator

from app import celery
from utils.mongo import Tasks
from utils.token import AccessToken
from utils.status import Task as TaskStatus
from . import errors


blueprint = Blueprint('task', __name__, url_prefix='/api/task')


# @blueprint.route("/", methods=["GET"])
# def tasks():
#     token = request.headers.get('token')
#
#     if token is None:
#         projection = {
#             'status': True,
#             'created': True,
#             'started': True,
#             'finished': True,
#             'offliner.name': True,
#             'offliner.config.mwUrl': True
#         }
#     else:
#         _ = JWT.decode(token)
#         projection = {
#             'status': True,
#             'created': True,
#             'started': True,
#             'finished': True,
#             'offliner': True,
#         }
#
#     limit = int(request.args.get('limit', 10))
#     offset = int(request.args.get('offset', 0))
#     sort = 1 if request.args.get('sort', -1) == 1 else -1
#
#     cursor = Tasks().aggregate([
#         {'$project': projection},
#         {'$sort': {'created': sort}},
#         {'$skip': offset},
#         {'$limit': limit},
#     ])
#     tasks = [task for task in cursor]
#
#     return jsonify({
#         'meta': {
#             'limit': limit,
#             'offset': offset
#         },
#         'items': tasks
#     })


@blueprint.route("/mwoffliner", methods=["POST"])
def enqueue_mwoffliner():
    """
    Enqueue mwoffliner tasks

    [Header] token: the access token to validate
    [Body] json array: mwoffliner task configurations
    :return:
    """
    def validate_task(config: dict):
        schema = {
            'mwUrl': {'type': 'string', 'required': True},
            'adminEmail': {'type': 'string', 'required': True},
            'verbose': {'type': 'boolean', 'required': False}
        }
        validator = Validator(schema, allow_unknown=True)

        if validator.validate(config):
            return None
        else:
            return validator.errors

    def enqueue_task(config: dict):
        document = {
            'status': TaskStatus.PENDING.name,
            'termination_time': None,
            'offliner': {
                'name': "mwoffliner",
                'config': config
            },
            'logs': []
        }
        validator = Validator(Tasks.schema)
        if not validator.validate(document):
            raise errors.TaskDocumentNotValid(validator.errors)

        result = Tasks().insert_one(document)
        task_id = result.inserted_id

        celery.send_task('mwoffliner', task_id=str(task_id), kwargs={'offliner_config': config})

    # check token exist and is valid
    token = AccessToken.decode(request.headers.get('access-token'))
    if token is None:
        raise errors.BadRequest()

    # check user can create tasks
    if not token.get('scope', {}).get('task', {}).get('create', False):
        raise errors.NotEnoughPrivilege()

    # check request is a list
    configs = request.get_json()
    if not isinstance(configs, list):
        raise errors.BadRequest('A list of task config is required.')

    # check each item in request is a valid mwoffliner config
    config_error = errors.OfflinerConfigNotValid()
    for index, config in enumerate(configs):
        validation_errors = validate_task(config)
        if validation_errors is not None:
            config_error.errors[index] = validation_errors
    if len(config_error.errors) > 0:
        raise config_error

    return Response(status=202)


# @blueprint.route("/<string:id>", methods=["GET", "PUT", "DELETE"])
# def task(id: str):
#     """
#
#     PUT: update task data
#     required:
#     status: the key for task status enum
#     """
#     # check token exist and is valid
#     jwt = JWT.decode(request.headers.get('token'))
#     if jwt is None:
#         raise errors.BadRequest()
#
#     if id is None or id == '':
#         raise errors.BadRequest('task id is required')
#
#     if request.method == 'GET':
#         task = Tasks().find_one({'_id': ObjectId(id)})
#         return jsonify(task)
#     elif request.method == 'DELETE':
#         # only admins can delete a task
#         if not jwt.is_admin:
#             raise errors.NotEnoughPrivilege()
#
#         Tasks().delete_one({'_id': ObjectId(id)})
#         return Response()