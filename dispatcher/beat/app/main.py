import os
from datetime import timedelta

from celery import Celery

from schedules import Scheduler

if __name__ == '__main__':
    system_username = 'system'
    system_password = os.getenv('SYSTEM_PASSWORD', '')
    url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(username=system_username, password=system_password)

    app = Celery(main='zimfarm', broker=url)
    app.conf.beat_scheduler = Scheduler
    app.conf.beat_max_loop_interval = timedelta(minutes=2).seconds
    app.start(argv=['celery', 'beat', '--loglevel', 'debug'])
