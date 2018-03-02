import random
import string
from celery import Celery

dispatcher_username = 'dispatcher'
dispatcher_password = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(32)])

celery = Celery(broker='amqp://{username}:{password}@rabbit:5672/{vhost}'.format(
        username=dispatcher_username, password=dispatcher_password, vhost='zimfarm'))
celery.conf.task_send_sent_event = True
