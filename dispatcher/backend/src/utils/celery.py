import os

from celery import Celery as CeleryBase
from kombu import Queue, Exchange


class Celery(CeleryBase):
    def __init__(self):
        system_username = 'system'
        system_password = os.getenv('SYSTEM_PASSWORD','')
        url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(username=system_username,
                                                                        password=system_password)
        super().__init__(main='zimfarm', broker=url)

        exchange = Exchange('offliner', 'topic')
        self.conf.task_queues = [
            Queue('small', exchange, routing_key='small'),
            Queue('medium', exchange, routing_key='medium'),
            Queue('large', exchange, routing_key='large'),
            Queue('debug', exchange, routing_key='debug'),
        ]
        self.conf.task_send_sent_event = True
