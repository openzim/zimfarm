from flask import Flask
from celery import Celery

from . import templates, tasks


def configure() -> (Flask):
    flask = Flask(__name__)
    flask.config['CELERY_BROKER_URL'] = 'pyamqp://celery:celery@localhost/celeryvhost'
    flask.config['CELERY_RESULT_BACKEND'] = 'rpc://'

    # celery = Celery(flask.name, broker=flask.config['CELERY_BROKER_URL'],
    #                 backend=flask.config['CELERY_RESULT_BACKEND'])
    # celery.conf.update(flask.config)

    return flask

app = configure()
app.route('/templates/list', methods=['GET'])(templates.list)
app.route('/templates/create', methods=['POST'])(templates.create)
app.route('/templates/update', methods=['POST'])(templates.update)
app.route('/tasks/enqueue', methods=['POST'])(tasks.enqueue)


if __name__ == "__main__":
    app.run()
