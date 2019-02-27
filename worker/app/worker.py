import logging
import sys

import paramiko
from celery import Celery
from kombu import Queue, Exchange

import tasks
from utils import Settings, SFTPClient


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
        self.credential_test()
        self.sftp_test()

        # configure celery broker
        broker_url = 'amqps://{username}:{password}@{host}:{port}/zimfarm'.format(
            username=Settings.username, password=Settings.password,
            host=Settings.dispatcher_hostname, port=Settings.rabbit_port)
        app = Celery(main='zimfarm_worker', broker=broker_url)

        # register tasks
        app.register_task(tasks.MWOffliner())

        # configure queues
        exchange = Exchange('offliner', 'topic')
        app.conf.task_queues = [
            Queue('small', exchange, routing_key='small'),
            Queue('medium', exchange, routing_key='medium'),
            Queue('large', exchange, routing_key='large'),
            Queue('debug', exchange, routing_key='debug')]

        # configure celery
        app.conf.worker_send_task_events = True
        app.conf.task_acks_late = True
        app.conf.task_reject_on_worker_lost = True
        app.conf.worker_concurrency = Settings.concurrency
        app.conf.worker_prefetch_multiplier = 1

        # start celery
        app.worker_main([
            'worker',
            '--hostname', '{}@{}'.format(Settings.username, Settings.node_name),
            '--queues', Settings.queues,
            '--loglevel', 'info',
            '-Ofair'
        ])

    def docker_test(self):
        # TODO: list containers to make sure have access to docker
        pass

    def credential_test(self):
        # TODO: make a simple request to validate username and password
        pass

    def sftp_test(self):
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
