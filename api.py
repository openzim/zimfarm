from flask import Flask
import flask_restful
from celery import Celery


def configure() -> (Flask, flask_restful.Api):
    flask = Flask(__name__)
    flask.config['CELERY_BROKER_URL'] = 'pyamqp://celery:celery@localhost/celeryvhost'
    flask.config['CELERY_RESULT_BACKEND'] = 'rpc://'

    api = flask_restful.Api(flask)

    celery = Celery(flask.name, broker=flask.config['CELERY_BROKER_URL'],
                    backend=flask.config['CELERY_RESULT_BACKEND'])
    celery.conf.update(flask.config)

    return flask, api

flask, api = configure()

if __name__ == "__main__":
    flask.run()
