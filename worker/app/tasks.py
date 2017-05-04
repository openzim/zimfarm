import time
import subprocess
from urllib import request, response, parse
import json
from celery import Celery, Task


app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672', backend='redis://redis:6379/0')


@app.task(name='delayed_add', track_started=True)
def delayed_add(x, y):
    print('delayed add begins: {} + {} = ??'.format(x, y))
    time.sleep(5)
    result = x + y
    print('delayed add finished: {} + {} = {}'.format(x, y, result))
    return result


@app.task(bind=True, name='subprocess', track_started=True)
def subprocess_run(self):
    def update_status(status, stdout):
        url = 'http://dispatcher:80/task/' + self.request.id
        payload = {
            'status': status,
            'stdout': stdout
        }
        req = request.Request(url,
                              headers={'content-type': 'application/json'},
                              data=json.dumps(payload).encode('utf-8'))
        response = request.urlopen(req)
        print(response.info())

    update_status('STARTED', None)
    time.sleep(5)
    process = subprocess.run(["ls", "-l", "/"], stdout=subprocess.PIPE, encoding='utf-8')
    update_status('FINISHED', process.stdout)