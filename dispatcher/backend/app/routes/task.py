from flask import Blueprint, request, jsonify

import database.task
from utils.token import UserJWT, MWOfflinerTaskJWT
from app import celery
from .error import exception
from utils.status import GenericTaskStatus


blueprint = Blueprint('task', __name__, url_prefix='/task')


@blueprint.route("/enqueue/zimfarm/generic", methods=["POST"])
def enqueue_zimfarm_generic():
    token = UserJWT.from_request_header(request)

    if not token.is_admin:
        raise exception.NotEnoughPrivilege()

    json = request.get_json()
    image_name = json.get('image_name')
    script = json.get('script')

    if image_name is None or script is None:
        raise exception.InvalidRequest()

    task_name = 'zimfarm.generic'
    kwargs = {
        'image_name': image_name,
        'script': script,
    }
    celery_task = celery.send_task(task_name, kwargs=kwargs)
    database_task = database.task.add(celery_task.id, task_name, GenericTaskStatus.PENDING, image_name, script)
    return jsonify(database_task), 202


@blueprint.route("/enqueue/zimfarm/mwoffliner", methods=["POST"])
def enqueue_mwoffliner():
    token = UserJWT.from_request_header(request)

    if not token.is_admin:
        raise exception.NotEnoughPrivilege()

    json = request.get_json()
    mw_url = json.get('mw_url')
    admin_email = json.get('admin_email')

    if mw_url is None or admin_email is None:
        raise exception.InvalidRequest()

    task_name = 'zimfarm.mwoffliner'
    celery_task = celery.send_task(task_name, kwargs={
        'token': MWOfflinerTaskJWT.new(),
        'params': json
    })
    # database_task = database.task.add(celery_task.id, task_name, GenericTaskStatus.PENDING)
    return jsonify(), 202


@blueprint.route("/list", methods=["GET"])
def list_tasks():
    token = UserJWT.from_request_header(request)

    limit = request.args.get('limit', 10)
    offset = request.args.get('limit', 0)

    tasks = database.task.get_all(limit, offset)
    return jsonify({
        'limit': limit,
        'offset': offset,
        'tasks': tasks
    })


@blueprint.route("/<string:id>", methods=["GET", "PUT"])
def task_detail(id):
    if request.method == 'GET':
        _ = UserJWT.from_request_header(request)
        task = database.task.get(id)
        if task is None:
            raise exception.TaskDoesNotExist()
        return jsonify(task)
    elif request.method == 'PUT':
        task = request.get_json()
        status = GenericTaskStatus[task.get('status')]
        stdout = task.get('stdout')
        stderr = task.get('stderr')
        return_code = task.get('return_code')
        database.task.update(id, status, stdout, stderr, return_code)
        return jsonify(), 204
