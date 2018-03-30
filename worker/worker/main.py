import sys
from pathlib import Path
from argparse import ArgumentParser
from celery import Celery

import tasks
from utils import Setting


def main():
    pass
    # parser = ArgumentParser(description='Zimfarm Worker')
    # parser.add_argument('--dockerized', dest='dockerized', action='store_true')
    # parser.add_argument('--version', action='version', version='0.1')
    # args = parser.parse_args()
    # dockerized = args.dockerized
    #
    # # banner

    #
    # # settings
    # if dockerized:

    # else:
    #     Setting.interactive = False
    #     Setting.read_from_cache()
    #     Setting.prompt_user()
    #     Setting.save_to_cache()
    #
    # check docker socket exists
    # docker_socket = Path('/var/run/docker.sock')
    # if not docker_socket.exists():
    #     if dockerized:
    #         print('Error: cannot find docker socket at {}, '
    #               'have you forgot to map it to the container?'.format(str(docker_socket)))
    #         sys.exit(1)
    #     else:
    #         sys.exit('Error: cannot find docker socket at {}, '
    #                  'have you installed docker yet?'.format(str(docker_socket)))
    #
    # # starting



if __name__ == "__main__":
    main()
