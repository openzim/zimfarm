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


class SchedulerEntry(beat.ScheduleEntry):

    logger = get_logger(__name__)

    def __init__(self, id: ObjectId, name: str, task_name: str, last_run_at: datetime,
                 total_run_count: int, schedule: BaseSchedule, app: Celery, *args, **kwargs):
        self.id = id
        super().__init__(name=name, task=task_name, last_run_at=last_run_at, total_run_count=total_run_count,
                         schedule=schedule, args=args, kwargs=kwargs, options={}, app=app)

    @classmethod
    def from_document(cls, app: Celery, document: dict) -> Optional['SchedulerEntry']:
        """Create an instance from a mongo document"""

        schedule_id = document.get('_id')
        schedule_name = document.get('name')
        task_name = document.get('task', {}).get('name')

        offliner_config = document.get('offliner', {}).get('config', None)
        last_run = document.get('last_run', None)
        total_run = document.get('total_run', 0)

        if schedule_id is None or schedule_name is None or task_name is None or offliner_config is None:
            return None

        schedule = cls.get_schedule(document)
        if schedule is None:
            return None

        return cls(schedule_id, schedule_name, task_name, last_run, total_run, schedule, app, offliner_config=offliner_config)

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

        timestamp = datetime.utcnow().replace(tzinfo=pytz.utc)

        Schedules().update_one(
            {'name': self.name},
            {'$set': {'last_run': timestamp, 'total_run': self.total_run_count + 1}})
        task_id = Tasks().insert_one({
            'schedule_id': self.id,
            'debug': True,
            'timestamp': {
                'created': timestamp
            }
        }).inserted_id

        document = Schedules().find_one({'name': self.name})
        schedule = self.__class__.from_document(self.app, document)
        schedule.kwargs['task_id'] = str(task_id)

        return schedule
