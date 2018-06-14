from celery import Celery
from celery.beat import Scheduler, ScheduleEntry
from celery.utils.log import get_logger


class MongoSchedulerEntry(ScheduleEntry):
    def __init__(self, app: Celery):
        super().__init__(app=app, task='add', name='test_entry')
        self.logger = get_logger('zimfarm')
        self.logger.info("MongoSchedulerEntry init")

    def is_due(self):
        self.logger.info("is_due called")
        return False, 5



class MongoScheduler(Scheduler):
    Entry = ScheduleEntry

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger('zimfarm')


        entry = ScheduleEntry(name='test', task='add', last_run_at=None,
                              total_run_count=0, schedule=100, relative=False, app=self.app)
        self.schedule[entry.name] = entry
        self.logger.info(set(self.schedule))

    def sync(self):
        entries: [ScheduleEntry] = []
        # populate `entries`
        self.merge_inplace(entries)


if __name__ == '__main__':

    app = Celery(main='zimfarm', broker='amqps://{username}:{password}@{host}:{port}/zimfarm'
                 .format(username='admin', password='admin_pass',
                         host='farm.openzim.org', port=5671))
    app.conf.beat_scheduler = MongoScheduler
    app.conf.beat_max_loop_interval = 1
    app.start(argv=['celery', 'beat', '-l', 'debug'])
