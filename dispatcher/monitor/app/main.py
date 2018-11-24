import logging
import os

from celery import Celery

from monitor import Monitor

if __name__ == '__main__':
    # configure logging
    logging.basicConfig(level=logging.INFO,
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
    monitor = Monitor(celery)
    monitor.start()