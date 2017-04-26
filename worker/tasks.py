from celery import Celery
import time


app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672', backend='rpc://')


@app.task(name='delayed_add')
def delayed_add(x, y):
	print('delayed add begins: {} + {} = ??'.format(x, y))
	time.sleep(5)
	result = x + y
	print('delayed add finished: {} + {} = {}'.format(x, y, result))
	return result