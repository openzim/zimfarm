import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from celery import Celery


flask = Flask(__name__)
flask.config.update({
    'SQLALCHEMY_DATABASE_URI': 'sqlite:////dispatcher_data/zimfarm.sqlite',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
})

db = SQLAlchemy(flask)

broker_url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(
    username=os.getenv('DISPATCHER_USERNAME'), password=os.getenv('DISPATCHER_PASSWORD'))
celery = Celery(main='dispatcher', broker=broker_url)


from JSONEncoder import ZimfarmDispatcherJSONEncoder
flask.json_encoder = ZimfarmDispatcherJSONEncoder