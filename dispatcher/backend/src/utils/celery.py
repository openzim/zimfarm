import os
from celery import Celery as CeleryBase


class Celery(CeleryBase):
    def __init__(self):
        system_username = 'system'
        system_password = os.getenv('SYSTEM_PASSWORD','')
        url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(username=system_username,
                                                                        password=system_password)
        super().__init__(main='zimfarm', broker=url)
