import os
from celery import Celery
from flask import Flask

from utils.json_encoder import ZimfarmEncoder


flask = Flask(__name__)
flask.json_encoder = ZimfarmEncoder

broker_url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(
    username=os.getenv('DISPATCHER_USERNAME'), password=os.getenv('DISPATCHER_PASSWORD'))
celery = Celery(main='dispatcher', broker=broker_url)
