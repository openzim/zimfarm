import sys
from pathlib import Path
from argparse import ArgumentParser
from celery import Celery

from . import tasks
from .utils import Setting


def main(dockerized: bool=False):
    # banner
    print("=========================================================\n",
          "Welcome to Zimfarm worker:\n",
          "=========================================================\n", sep='')

    # settings
    if dockerized:
        Setting.dockerized = True
        Setting.read_from_env()
    else:
        Setting.dockerized = False
        Setting.read_from_cache()
        Setting.prompt_user()
        Setting.save_to_cache()

    # check docker socket exists
    docker_socket = Path('/var/run/docker.sock')
    if not docker_socket.exists():
        if dockerized:
            print('Error: cannot find docker socket at {}, '
                  'have you forgot to map it to the container?'.format(str(docker_socket)))
            sys.exit(1)
        else:
            sys.exit('Error: cannot find docker socket at {}, '
                     'have you installed docker yet?'.format(str(docker_socket)))

    # starting
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


if __name__ == "__main__":
    parser = ArgumentParser(description='Zimfarm Worker')
    parser.add_argument('--dockerized', dest='dockerized', action='store_true')
    parser.add_argument('--version', action='version', version='0.1')
    args = parser.parse_args()

    main(dockerized=args.dockerized)
