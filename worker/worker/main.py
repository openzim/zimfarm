import sys
from pathlib import Path
from argparse import ArgumentParser
from celery import Celery

import tasks
from utils import Setting

#
# def main():
#     pass
    # parser = ArgumentParser(description='Zimfarm Worker')
    # parser.add_argument('--dockerized', dest='dockerized', action='store_true')
    # parser.add_argument('--version', action='version', version='0.1')
    # args = parser.parse_args()
    # dockerized = args.dockerized
    #
#
#
# if __name__ == "__main__":
#     main()
