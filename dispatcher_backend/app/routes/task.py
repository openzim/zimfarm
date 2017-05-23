from flask import request, jsonify
from app import celery
import database.task


def hello():
    return "Hello World from zim farm using Python 3.5"


def subprocess():
    request_data = request.get_json()
    command = request_data['command']
    
    task_name = 'subprocess'
    celery_task = celery.send_task(task_name, kwargs={'command': command})
    database_task = database.task.add(celery_task.id, task_name, 'PENDING', command)
    return jsonify(database_task)


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
        returncode = request_data.get('returncode')
        stdout = request_data.get('stdout')
        stderr = request_data.get('stderr')
        error = request_data.get('error')

        task = database.task.update(id, status, command, returncode, stdout, stderr, error)
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