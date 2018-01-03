import os
from celery import Celery

broker_url = 'amqp://{username}:{password}@rabbit:5672/{vhost}'.format(
        username=os.getenv('RABBITMQ_DEFAULT_USER'),
        password=os.getenv('RABBITMQ_DEFAULT_PASS'),
        vhost=os.getenv('RABBITMQ_DEFAULT_VHOST'))
celery = Celery(main='dispatcher', broker=broker_url)