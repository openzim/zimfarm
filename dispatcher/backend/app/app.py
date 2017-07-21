import os

from celery import Celery
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

flask = Flask(__name__)
flask.config.update({
    'SQLALCHEMY_DATABASE_URI': 'sqlite:////data/zimfarm.sqlite',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
})

db = SQLAlchemy(flask)

broker_url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(
    username=os.getenv('DISPATCHER_USERNAME'), password=os.getenv('DISPATCHER_PASSWORD'))
celery = Celery(main='dispatcher', broker=broker_url)


from utils.json_encoder import ZimfarmDispatcherJSONEncoder
flask.json_encoder = ZimfarmDispatcherJSONEncoder