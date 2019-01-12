import logging
import os
from time import sleep

from amqp.exceptions import AccessRefused
from celery import Celery

from monitor import Monitor

if __name__ == '__main__':
    # configure logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler('/worker.log', mode='w')])

    # configure celery
    system_username = 'system'
    system_password = os.getenv('SYSTEM_PASSWORD', '')
    broker_url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(
        username=system_username, password=system_password)
    celery = Celery(broker=broker_url)

    # start monitor
    retries = 3
    while retries:
        try:
            monitor = Monitor(celery)
            monitor.start()
        except AccessRefused:
            sleep(2)
        finally:
            retries -= 1
    else:
        logger = logging.getLogger(__name__)
        logger.error('Failed to start celery monitor')
        exit(1)
