from datetime import datetime
from enum import Enum
from typing import Optional

import pytz
from bson import ObjectId

from common.mongo import Tasks, Schedules
from utils.celery import Celery


class ScheduleService:
    @classmethod
    def send_task(cls, schedule_name: str) -> Optional[ObjectId]:
        """Send a schedule into queue

        :param schedule_name:
        :return: task id
        """

        schedule = Schedules().find_one({'name': schedule_name}, {'config': 1})
        id = schedule.get('_id')
        config = schedule.get('config')

        if id and config:
            task_id = Tasks().insert_one({
                'schedule_id': id,
                'timestamp': {'created': datetime.utcnow().replace(tzinfo=pytz.utc)}
            }).inserted_id

            task_name = config.get('task_name')
            queue = config.get('queue')

            task_kwargs = {
                'flags': config.get('flags'),
                'image': config.get('image'),
                'queue': queue,
                'warehouse_path': config.get('warehouse_path')
            }

            celery = Celery()
            celery.send_task(name=task_name, args=(), kwargs=task_kwargs, task_id=str(task_id),
                             exchange='offliner', routing_key=queue)

            return task_id
        else:
            return None


class ScheduleCategory(Enum):
    wikipedia = 'wikipedia'
    phet = 'phet'

    @classmethod
    def all(cls) -> ['ScheduleCategory']:
        return [
            cls.wikipedia,
            cls.phet
        ]

    @classmethod
    def all_values(cls) -> [str]:
        return [category.value for category in cls.all()]
