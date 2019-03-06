import os
from typing import Optional

from celery import Celery as CeleryBase
from kombu import Queue, Exchange


class Celery(CeleryBase):
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, port: Optional[int] = None):
        username = username if username else 'system'
        password = password if password else os.getenv('SYSTEM_PASSWORD','')
        port = port if port else 5672

        url = 'amqp://{username}:{password}@rabbit:{port}/zimfarm'.format(
            username=username, password=password, port=port)
        super().__init__(main='zimfarm', broker=url)

        exchange = Exchange('offliner', 'topic')
        self.conf.task_queues = [
            Queue('small', exchange, routing_key='small'),
            Queue('medium', exchange, routing_key='medium'),
            Queue('large', exchange, routing_key='large'),
            Queue('debug', exchange, routing_key='debug'),
        ]
        self.conf.task_send_sent_event = True
