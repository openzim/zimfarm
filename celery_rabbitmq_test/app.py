from celery import Celery
import time

app = Celery('celery_test', broker='amqp://admin:mypass@10.211.55.12:5672', backend='rpc://')

@app.task
def longtime_add(x, y):
	time.sleep(5)
	return x + y

if __name__ == 'main':
    for i in range(10):
		res = longtime_add.delay(i, i+1)
		time.sleep(1)
