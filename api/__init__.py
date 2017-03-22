from flask import Flask
from celery import Celery


def configure() -> (Flask):
    flask = Flask(__name__)
    flask.config['CELERY_BROKER_URL'] = 'pyamqp://celery:celery@localhost/celeryvhost'
    flask.config['CELERY_RESULT_BACKEND'] = 'rpc://'
    flask.config['SQLITE_PATH'] = '/Volumes/Data/zimfarm_test.sqlite'
    # celery = Celery(flask.name, broker=flask.config['CELERY_BROKER_URL'],
    #                 backend=flask.config['CELERY_RESULT_BACKEND'])
    # celery.conf.update(flask.config)

    return flask

app = configure()

from . import templates, task, database


if __name__ == "__main__":
    app.run()
