import os
import sys
import amqp
from datetime import timedelta
from time import sleep

from pymongo.errors import ServerSelectionTimeoutError
from celery import Celery

from mongo import Client
from schedules import Scheduler
from kombu import Queue, Exchange


def check_mongo_booted() -> bool:
    retries = 3
    while retries > 0:
        try:
            client = Client()
            client.server_info()
            return True
        except ServerSelectionTimeoutError:
            retries -= 1
            sleep(10)
    return False


if __name__ == '__main__':
    if not check_mongo_booted():
        sys.exit(1)

    system_username = 'system'
    system_password = os.getenv('SYSTEM_PASSWORD', '')
    url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(username=system_username, password=system_password)

    app = Celery(main='zimfarm', broker=url)

    # configure beat
    app.conf.beat_scheduler = Scheduler
    app.conf.beat_max_loop_interval = timedelta(minutes=2).seconds

    # configure queue
    offliner_exchange = Exchange('offliner', 'topic')
    app.conf.task_queues = [
        Queue('offliner_tiny', offliner_exchange, routing_key='#.small'),
        Queue('offliner_small', offliner_exchange, routing_key='#.small'),
        Queue('offliner_medium', offliner_exchange, routing_key='#.small'),
        Queue('offliner_large', offliner_exchange, routing_key='#.small'),
        Queue('offliner_gigantic', offliner_exchange, routing_key='#.small'),
    ]

    retries = 3
    while retries < 3:
        try:
            app.start(argv=['celery', 'beat', '--loglevel', 'debug'])
        except amqp.exceptions.AccessRefused:
            retries -= 1
            sleep(2)
