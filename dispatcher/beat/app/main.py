import os
from datetime import datetime, timedelta
from typing import Optional

from celery import Celery
from celery.beat import Scheduler, ScheduleEntry, crontab
from celery.schedules import BaseSchedule
from celery.utils.log import get_logger

from mongo import Schedules


class MongoSchedulerEntry(ScheduleEntry):
    def __init__(self, name: str, task_name: str, last_run_at: datetime,
                 total_run_count: int, schedule: BaseSchedule, app: Celery, *args, **kwargs):
        super().__init__(name=name, task=task_name, last_run_at=last_run_at, total_run_count=total_run_count,
                         schedule=schedule, args=args, kwargs=kwargs, options={}, app=app)
        self.logger = get_logger('zimfarm')

    @classmethod
    def from_document(cls, app: Celery, document: dict):
        schedule_name = document.get('name', None)
        task_name = document.get('task', {}).get('name', None)

        offliner_config = document.get('offliner', {}).get('config', None)
        last_run = document.get('last_run', None)
        total_run = document.get('total_run', 0)

        if schedule_name is None or task_name is None or offliner_config is None:
            return None

        schedule = cls.get_schedule(document['beat'])
        if schedule is None:
            return None

        return cls(schedule_name, task_name, last_run, total_run, schedule, app, offliner_config=offliner_config)

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

    def __next__(self):
        Schedules().update_one({'name': self.name}, {'$set': {
                                   'last_run': self.app.now(),
                                   'total_run': self.total_run_count + 1
                               }})
        document = Schedules().find_one({'name': self.name})
        return self.__class__.from_document(self.app, document)


class MongoScheduler(Scheduler):
    Entry = ScheduleEntry
    last_update = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger('zimfarm')

    @property
    def schedule(self) -> dict:
        if self.last_update is not None and datetime.now() - self.last_update < timedelta(minutes=1):
            # will use cached data for very frequent access
            return self.data

        self.data = {document['name']: MongoSchedulerEntry.from_document(app=self.app, document=document)
                     for document in Schedules().find()}
        self.last_update = datetime.now()

        self.logger.debug('Schedules synced, count={}'.format(len(self.data)))
        return self.data


if __name__ == '__main__':
    system_username = 'system'
    system_password = os.getenv('SYSTEM_PASSWORD', '')
    url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(username=system_username, password=system_password)
    app = Celery(main='zimfarm', broker=url)
    app.conf.beat_scheduler = MongoScheduler
    app.conf.beat_max_loop_interval = timedelta(minutes=2).seconds
    app.start(argv=['celery', 'beat', '-l', 'debug'])
