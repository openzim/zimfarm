from celery import Celery
import time


app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672', backend='rpc://')


@app.task(name='test.add')
def longtime_add(x, y):
	print('long time task begins')
	time.sleep(5)
	print('long time task finished')
	return x + y