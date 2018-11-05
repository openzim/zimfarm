import sys
from pathlib import Path
from celery import Celery

from . import tasks
from .utils import Setting


class Worker:
    def __init__(self):
        pass

    def start(self):
        self.print_banner()
        self.read_setting()
        self.check_docker()
        self.start_celery()

    @staticmethod
    def print_banner():
        print("=========================================================\n",
              "Welcome to Zimfarm worker:\n",
              "=========================================================\n", sep='')

    @staticmethod
    def read_setting():
        Setting.read_from_env()

    @staticmethod
    def check_docker():
        docker_socket = Path('/var/run/docker.sock')
        if not docker_socket.exists():
            if Setting.interactive:
                print('Error: cannot find docker socket at {}, '
                      'have you installed docker yet?'.format(str(docker_socket)))
            else:
                print('Error: cannot find docker socket at {}, '
                      'have you forgot to map it to the container?'.format(str(docker_socket)))
            sys.exit(1)

    @staticmethod
    def start_celery():
        print("---------------------------------------------------------\n",
              "Starting...", sep='')

        app = Celery(main='zimfarm_worker', broker='amqps://{username}:{password}@{host}:{port}/zimfarm'
                     .format(username=Setting.username, password=Setting.password,
                             host=Setting.dispatcher_host, port=Setting.rabbitmq_port))
        app.register_task(tasks.MWOffliner())
        app.start(argv=['celery', 'worker',
                        '--task-events',
                        '-l', 'info',
                        '--concurrency', '1',
                        '-n', '{}@%h'.format(Setting.username)])