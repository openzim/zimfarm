from flask import request, jsonify
import jwt, utils
from app import celery
import database.task
from .exceptions import InvalidRequest, AuthFailed


def hello():
    return "Hello World from zim farm using Python 3.5"


def subprocess():
    try:
        request_data = request.get_json()
        token = request_data.get('token')
        script = request_data.get('script')

        if token is None or script is None:
            raise InvalidRequest()
            
        utils.jwt_decode(token)
        
        task_name = 'subprocess'
        celery_task = celery.send_task(task_name, kwargs={'script': script})
        database_task = database.task.add(celery_task.id, task_name, 'PENDING')
        return jsonify(database_task)
    except InvalidRequest:
        pass
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return jsonify({'success': False, 'message': 'token is not valid'}), 401

def mwoffliner():
    request_data = request.get_json()
    config = request_data.get('config')
    
    task_name = 'mwoffliner'
    celery_task = celery.send_task(task_name, kwargs={'config': config if config is not None else {}})
    database_task = database.task.add(celery_task.id, task_name, 'PENDING')
    return jsonify(database_task)


def task(id):
    if request.method == 'POST':
        request_data = request.get_json()

        status = request_data.get('status')
        command = request_data.get('command')
        return_code = request_data.get('return_code')
        stdout = request_data.get('stdout')
        stderr = request_data.get('stderr')
        error = request_data.get('error')

        task = database.task.update(id, status, command, return_code, stdout, stderr, error)
        response = {
            'success': True,
            'task': task
        }
        return jsonify(response)
    else:
        task = database.task.get(id)
        return jsonify(task) if task is not None else ('', 404)


def tasks():
    return jsonify(database.task.get_all())