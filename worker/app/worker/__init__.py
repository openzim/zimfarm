import logging
import sys

from celery import Celery

from . import tasks
from .utils import Settings


class Worker:
    logger = logging.getLogger(__name__)

    def __init__(self):
        pass

    def start(self):
        self.logger.info('Starting Zimfarm Worker...')

        # setting
        Settings.sanity_check()
        Settings.log()

        # check docker socket exists
        if not Settings.docker_socket_path.exists():
            self.logger.error('Cannot find docker socket at {}'.format(Settings.docker_socket_path))
            sys.exit(1)

        # start celery
        broker_url = 'amqps://{username}:{password}@{host}:{port}/zimfarm'.format(
            username=Settings.username, password=Settings.password,
            host=Settings.dispatcher_hostname, port=Settings.rabbit_port)
        celery = Celery(main='zimfarm_worker', broker=broker_url)
        celery.register_task(tasks.MWOffliner())
        celery.start(argv=['celery', 'worker',
                           '--task-events',
                           '-l', 'info',
                           '--concurrency', '1',
                           '-n', '{}@%h'.format(Settings.username)])
