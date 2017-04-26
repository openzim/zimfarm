from flask import Flask, jsonify
from celery import Celery

flask_app = Flask(__name__)
celery_app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672', backend='rpc://')

@flask_app.route("/")
def hello():
   return "Hello World [ccust] from Flask using Python 3.5"

@flask_app.route("/test")
def test():
    task = celery_app.send_task('delayed_add', args=[4, 7])
    response = {
        'task_id': task.id
    }
    return jsonify(response)

if __name__ == "__main__":
   flask_app.run(host='0.0.0.0', debug=True, port=80)