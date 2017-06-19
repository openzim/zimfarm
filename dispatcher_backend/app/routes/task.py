from flask import request, jsonify
# import jwt
from app import celery
import utils
import database.task
from .exceptions import InvalidRequest
from status import ZimfarmGenericTaskStatus


def hello():
    return "Hello World from zim farm using Python 3.5"


def zimfarm_generic():
    request_data = request.get_json()
    token = request_data.get('token')
    image_name = request_data.get('image_name')
    script = request_data.get('script')

    if token is None or image_name is None or script is None:
        raise InvalidRequest()

    utils.jwt_decode(token)

    task_name = 'zimfarm_generic'
    kwargs = {
        'image_name': image_name,
        'script': script
    }
    celery_task = celery.send_task(task_name, kwargs=kwargs)
    database_task = database.task.add(celery_task.id, task_name, ZimfarmGenericTaskStatus.PENDING, script)
    return jsonify(database_task)


def task(id):
    if request.method == 'POST':
        request_data = request.get_json()

        task_data = request_data.get('task')
        status = ZimfarmGenericTaskStatus[task_data.get('status')]
        stdout = task_data.get('stdout')
        stderr = task_data.get('stderr')
        return_code = task_data.get('return_code')

        database.task.update(id, status, stdout, stderr, return_code)
        return jsonify()
    else:
        task_data = database.task.get(id)
        return jsonify(task_data) if task_data is not None else ('', 404)


def tasks():
    return jsonify(database.task.get_all())