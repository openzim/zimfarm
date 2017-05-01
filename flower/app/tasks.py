from celery import Celery
import time


app = Celery('flower', broker='amqp://admin:mypass@rabbit:5672', backend='redis://redis:6379/0')


@app.task(name='delayed_add', track_started=True)
def delayed_add(x, y):
    print('delayed add begins: {} + {} = ??'.format(x, y))
    time.sleep(5)
    result = x + y
    print('delayed add finished: {} + {} = {}'.format(x, y, result))
    return result