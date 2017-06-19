from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from celery import Celery


flask = Flask(__name__)
flask.config.update({
    'SQLALCHEMY_DATABASE_URI': 'sqlite:////zimfarm.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
})
db = SQLAlchemy(flask)
celery = Celery('worker', broker='amqp://admin:mypass@rabbit:5672')


from JSONEncoder import ZimfarmDispatcherJSONEncoder
flask.json_encoder = ZimfarmDispatcherJSONEncoder