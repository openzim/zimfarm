import os

from utils.celery import Celery


def list(celery: Celery):
    print(celery.control.inspect(timeout=3).stats())


if __name__ == '__main__':
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    celery = Celery(username, password, 5671)
    list(celery)
