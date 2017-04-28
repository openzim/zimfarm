from flask import Flask, request, jsonify
import celery
from flower.utils.tasks import iter_tasks


flask_app = Flask(__name__)
celery_app = celery.Celery('worker', broker='amqp://admin:mypass@rabbit:5672', backend='redis://redis:6379/0')


@flask_app.route("/")
def hello():
   return "Hello World from zim farm using Python 3.5"


@flask_app.route("/task/delayed_add", methods=['POST'])
def task_delayed_add():
    request_json = request.get_json()
    x = request_json['x']
    y = request_json['y']
    name = 'delayed_add'
    task = celery_app.send_task(name, args=[x, y])
    response = {
        'task': {
            'id': task.id,
            'name': name,
            'status': task.status
        },
    }
    return jsonify(response)


@flask_app.route("/task/status/<string:id>")
def task_status(id):
    res = celery_app.AsyncResult(id)
    status = res.status
    response = {
        'id': id,
        'status': status,
    }
    if status == celery.states.SUCCESS:
        response['result'] = res.result
    return jsonify(response)


@flask_app.route("/tasks")
def get_tasks():
    events = celery_app.events
    t = iter_tasks(events)
    response = {
        "tasks": [2, 3, 4],
        "debug": print(type(t))
    }

    # for task_id, task in iter_tasks(events):
    #     tasks.append(task_id)
    return jsonify(response)

if __name__ == "__main__":
   flask_app.run(host='0.0.0.0', debug=True, port=80)