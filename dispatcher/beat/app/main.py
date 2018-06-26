import os
from datetime import datetime
from celery import Celery
from celery.beat import Scheduler, ScheduleEntry, crontab
from celery.schedules import BaseSchedule
from celery.utils.log import get_logger
from typing import Optional

from mongo import Schedules


class MongoSchedulerEntry(ScheduleEntry):
    def __init__(self, name: str, task: str, last_run_at: datetime,
                 total_run_count: int, schedule: BaseSchedule, app: Celery, *args, **kwargs):
        super().__init__(name=name, task=task, last_run_at=last_run_at, total_run_count=total_run_count,
                         schedule=schedule, args=args, kwargs=kwargs, app=app)
        self.logger = get_logger('zimfarm')

    @classmethod
    def from_document(cls, app: Celery, document: dict):
        name = document.get('name', None)
        task_name = document.get('task', {}).get('name', None)
        task_config = document.get('task', {}).get('config', None)
        last_run = document.get('last_run', None)
        total_run = document.get('total_run', 0)

        if name is None or task_name is None:
            return None

        schedule = cls.get_schedule(document['beat'])
        if schedule is None:
            return None

        return cls(name, task_name, last_run, total_run, schedule, app, kwargs={'config': task_config})

    @staticmethod
    def get_schedule(beat: dict) -> Optional[BaseSchedule]:
        type = beat['type']
        config = beat['config']
        if type == 'crontab':
            return crontab(minute=config.get('minute', '*'),
                           hour=config.get('hour', '*'),
                           day_of_week=config.get('day_of_week', '*'),
                           day_of_month=config.get('day_of_month', '*'),
                           month_of_year=config.get('month_of_year', '*'))
        else:
            return None


class MongoScheduler(Scheduler):
    Entry = ScheduleEntry

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger('zimfarm')

    @property
    def schedule(self) -> dict:
        entries = {}

        cursor = Schedules().find()
        for schedule in cursor:
            entry = MongoSchedulerEntry.from_document(app=self.app, document=schedule)
            entries[entry.name] = entry
        self.data = entries

        self.logger.info('schedule updated, count={}'.format(len(self.data)))
        self.logger.info(list(self.data.values())[0])
        return self.data


if __name__ == '__main__':
    system_username = 'system'
    system_password = os.getenv('SYSTEM_PASSWORD', '')
    url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(username=system_username,
                                                                    password=system_password)
    app = Celery(main='zimfarm', broker=url)
    app.conf.beat_scheduler = MongoScheduler
    app.conf.beat_max_loop_interval = 600
    app.start(argv=['celery', 'beat', '-l', 'debug'])
