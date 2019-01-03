import logging
import sys

import paramiko
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

        # test
        self.credential_smoke_test()
        self.sftp_smoke_test()

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
                           '-n', '{}@{}'.format(Settings.username, Settings.node_name)])

    def docker_smoke_test(self):
        # TODO: list containers to make sure have access to docker
        pass

    def credential_smoke_test(self):
        # TODO: make a simple request to validate username and password
        pass

    def sftp_smoke_test(self):
        try:
            hostname = Settings.warehouse_hostname
            port = Settings.warehouse_port
            username = Settings.username
            private_key = Settings.private_key
            with SFTPClient(hostname, port, username, private_key) as client:
                client.list_dir('/')
            self.logger.info('SFTP auth check success.')
        except paramiko.AuthenticationException:
            self.logger.error('SFTP auth check failed -- please double check your username and private key.')
            sys.exit(1)
