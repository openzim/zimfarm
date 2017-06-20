from flask import request, jsonify
import jwt
from app import celery
import utils
import database.task
from .exceptions import InvalidRequest
from status import GenericTaskStatus


def validate_token(token):
    if token is None:
        raise InvalidRequest()
    utils.jwt_decode(token)


def enqueue_zimfarm_generic():
    try:
        validate_token(request.headers.get('token'))

        request_json = request.get_json()
        image_name = request_json.get('image_name')
        script = request_json.get('script')

        if image_name is None or script is None:
            raise InvalidRequest()

        task_name = 'zimfarm_generic'
        kwargs = {
            'image_name': image_name,
            'script': script
        }
        celery_task = celery.send_task(task_name, kwargs=kwargs)
        database_task = database.task.add(celery_task.id, task_name, GenericTaskStatus.PENDING,
                                          image_name, script)
        return jsonify(database_task), 202
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return jsonify({'error': 'token invalid or expired'}), 401


def task_detail(id):
    if request.method == 'POST':
        request_data = request.get_json()

        task_data = request_data.get('task')
        status = GenericTaskStatus[task_data.get('status')]
        stdout = task_data.get('stdout')
        stderr = task_data.get('stderr')
        return_code = task_data.get('return_code')

        database.task.update(id, status, stdout, stderr, return_code)
        return jsonify()
    else:
        try:
            validate_token(request.headers.get('token'))
            task_data = database.task.get(id)
            return jsonify(task_data) if task_data is not None else ('', 404)
        except (jwt.DecodeError, jwt.ExpiredSignatureError):
            return jsonify({'error': 'token invalid or expired'}), 401


def list_tasks():
    try:
        validate_token(request.headers.get('token'))
        return jsonify(database.task.get_all())
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return jsonify({'error': 'token invalid or expired'}), 401

