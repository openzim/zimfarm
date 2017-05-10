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
    return jsonify({'task': database_task})


def task(id):
    if request.method == 'POST':
        request_data = request.get_json()
        status = request_data.get('status')
        stdout = request_data.get('stdout')
        stderr = request_data.get('stderr')
        task = database.task.update(id, status, stdout, stderr)
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

def on_raw_message(body):
    print(body)