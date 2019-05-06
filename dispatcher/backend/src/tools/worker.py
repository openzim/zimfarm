import os

from celery import Celery


def retrieve(celery: Celery):
    print(celery.control.inspect(timeout=3).stats())


def purge(celery: Celery):
    celery.control.purge()


if __name__ == '__main__':
    url = 'amqps://{username}:{password}@farm.openzim.org:{port}/zimfarm'.format(
        username='automactic', password='macOS10&open', port=5671)

    celery = Celery(main='zimfarm', broker=url)
    purge(celery)
