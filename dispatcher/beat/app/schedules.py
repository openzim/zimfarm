from datetime import datetime, timedelta
from typing import Optional

import pytz
from bson import ObjectId
from celery import Celery, beat, schedules
from celery.schedules import BaseSchedule
from celery.utils.log import get_logger

from mongo import Schedules, Tasks


class Scheduler(beat.Scheduler):
    """Schedule Manager"""

    logger = get_logger(__name__)

    def __init__(self, *args, **kwargs):
        self.last_update: Optional[datetime] = None
        self.cached = {}
        super().__init__(*args, **kwargs)

    @property
    def schedule(self) -> dict:
        # if last update from database is within 1 min from now, use cached schedules directly
        if self.last_update is not None and datetime.now() - self.last_update < timedelta(minutes=1):
            return self.cached

        # update cached schedules
        self.cached = {}
        for document in Schedules().find({'enabled': True}):
            schedule = SchedulerEntry.from_document(app=self.app, document=document)
            if schedule is None:
                continue
            self.cached[schedule.name] = schedule
        self.last_update = datetime.now()

        self.logger.debug('Schedules synced, count={}'.format(len(self.cached)))
        return self.cached

    def send_task(self, *args, **kwargs):
        """
        Override the send_task function of the base class.
        Inserting a task document and set the document id as task id.
        """

        schedule_id = kwargs.get('schedule_id')
        if schedule_id:
            task_id = Tasks().insert_one({
                'schedule_id': schedule_id,
                'debug': True,
                'timestamp': {
                    'created': datetime.utcnow().replace(tzinfo=pytz.utc)
                }
            }).inserted_id
            kwargs['task_id'] = str(task_id)

        return super().send_task(*args, **kwargs)


class SchedulerEntry(beat.ScheduleEntry):

    logger = get_logger(__name__)

    def __init__(self, schedule_id: ObjectId, name: str, task_name: str, last_run_at: datetime, total_run_count: int,
                 schedule: BaseSchedule, app: Celery, task_args: tuple, task_kwargs: dict, task_options: dict):
        task_options['schedule_id'] = schedule_id
        super().__init__(name=name, task=task_name, last_run_at=last_run_at, total_run_count=total_run_count,
                         schedule=schedule, args=task_args, kwargs=task_kwargs, options=task_options, app=app)
        self.id = schedule_id

    @classmethod
    def from_document(cls, app: Celery, document: dict) -> Optional['SchedulerEntry']:
        """Create an instance from a mongo document"""

        schedule_id = document.get('_id')
        schedule_name = document.get('name')
        task_options = document.get('celery', {})
        task_name = task_options.pop('task_name')

        task_config = document.get('task', {})
        last_run = document.get('last_run', None)
        total_run = document.get('total_run', 0)

        if schedule_id is None or schedule_name is None or task_name is None or task_config is None:
            return None

        schedule = cls.get_schedule(document)
        if schedule is None:
            return None

        return cls(schedule_id, schedule_name, task_name, last_run, total_run, schedule, app,
                   task_args=(), task_kwargs=task_config, task_options=task_options)

    @staticmethod
    def get_schedule(document: dict) -> Optional[BaseSchedule]:
        """Return a `BaseSchedule` based on what type the schedule is"""

        beat_type = document.get('beat', {}).get('type')
        config = document.get('beat', {}).get('config')

        if beat_type == 'crontab':
            try:
                return beat.crontab(minute=config.get('minute', '*'),
                                    hour=config.get('hour', '*'),
                                    day_of_week=config.get('day_of_week', '*'),
                                    day_of_month=config.get('day_of_month', '*'),
                                    month_of_year=config.get('month_of_year', '*'))
            except schedules.ParseException:
                return None
        else:
            return None

    def __next__(self):
        """Return the next instance"""

        Schedules().update_one(
            {'name': self.name},
            {'$set': {'last_run': datetime.utcnow().replace(tzinfo=pytz.utc), 'total_run': self.total_run_count + 1}})
        document = Schedules().find_one({'name': self.name})
        return self.__class__.from_document(self.app, document)
