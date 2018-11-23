import logging

from celery import Celery

from monitor import Monitor

if __name__ == '__main__':
    # configure logging
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler('/worker.log', mode='w')])
    logging.getLogger("paramiko").setLevel(logging.WARNING)

    # configure celery
    broker_url = 'amqps://{username}:{password}@farm.openzim.org:5671/zimfarm'.format(
        username='automactic', password='macOS10&open')
    celery = Celery(broker=broker_url)

    # start monitor
    monitor = Monitor(celery)
    monitor.start()