import os
import random
import string
from celery import Celery as CeleryBase


class Celery(CeleryBase):
    def __init__(self):
        system_username = 'system'
        system_password = os.getenv('SYSTEM_PASSWORD',
                                    ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)]))
        url = 'amqp://{username}:{password}@rabbit:5672/zimfarm'.format(username=system_username,
                                                                        password=system_password)
        celery = CeleryBase(main='zimfarm', broker=url)
