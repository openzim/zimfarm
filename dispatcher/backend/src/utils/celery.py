import os
from typing import Optional

from bson import ObjectId
from celery import Celery as CeleryBase
from kombu import Queue, Exchange

from common.mongo import Schedules, Tasks


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

    def send_task_from_schedule(self, schedule_name: str) -> Optional[ObjectId]:
        """Send a schedule into queue from a schedule.

        :param schedule_name:
        :return: task_id
        """

        schedule = Schedules().find_one({'name': schedule_name}, {'config': 1})
        id = schedule['_id']
        config = schedule.get('config')

        if not config:
            return None

        task_id = Tasks().insert_one({'schedule': {'_id': id, 'name': schedule_name}}).inserted_id

        task_name = config.get('task_name')
        queue = config.get('queue')

        task_kwargs = {
            'flags': config.get('flags'),
            'image': config.get('image'),
            'queue': queue,
            'warehouse_path': config.get('warehouse_path')
        }

        self.send_task(name=task_name, args=(), kwargs=task_kwargs, task_id=str(task_id),
                       exchange='offliner', routing_key=queue)

        return task_id
