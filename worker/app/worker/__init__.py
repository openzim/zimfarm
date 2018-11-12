import logging
import sys

from celery import Celery

from . import tasks
from .utils import Settings, SFTPClient


class Worker:
    logger = logging.getLogger(__name__)

    def __init__(self):
        pass

    def start(self):
        self.logger.info('Starting Zimfarm Worker...')

        # setting
        Settings.sanity_check()
        Settings.ensure_correct_typing()
        Settings.log()

        # sftp smoke test
        hostname = Settings.warehouse_hostname
        port = Settings.warehouse_port
        username = Settings.username
        private_key = Settings.private_key
        with SFTPClient(hostname, port, username, private_key) as client:
            contents = client.list_dir('/')
            # TODO: handle test failure


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
