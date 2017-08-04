import os
from celery import Celery
from flask import Flask

from utils.json_encoder import ZimfarmEncoder


flask = Flask(__name__)
flask.json_encoder = ZimfarmEncoder

broker_url = 'amqp://{username}:{password}@rabbit:5672/{vhost}'.format(
    username=os.getenv('RABBITMQ_DEFAULT_USER'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS'),
    vhost=os.getenv('RABBITMQ_DEFAULT_VHOST'))
celery = Celery(main='dispatcher', broker=broker_url)
