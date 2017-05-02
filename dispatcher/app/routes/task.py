from flask import request, jsonify
from app import celery
import database.task


def hello():
   return "Hello World from zim farm using Python 3.5"


def delayed_add():
    request_data = request.get_json()
    x = request_data['x']
    y = request_data['y']

    task_name = 'delayed_add'
    task = celery.send_task(task_name, args=[x, y])
    database.task.add(task.id, task_name)

    response = {
        'task': {
            'id': task.id,
            'name': task_name,
            'status': task.status
        },
    }
    return jsonify(response)


def status(id):
    result = celery.AsyncResult(id)
    status = result.status
    response = {
        'id': id,
        'status': status,
    }
    if status == 'SUCCESS':
        response['result'] = result.result
    return jsonify(response)


def tasks():
    tasks = [*map(lambda x: {
        'id': x.id,
        'name': x.name,
    }, database.task.get_all())]

    response = {
        'tasks': tasks
    }
    return jsonify(response)