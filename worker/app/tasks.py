import time
import subprocess
from urllib import request, response, parse
import json
from celery import Celery, Task


app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672', backend='redis://redis:6379/0')


@app.task(bind=True, name='subprocess', track_started=True)
def subprocess_run(self, command: str):
    def update_status(status, stdout):
        url = 'http://proxy/api/task/' + self.request.id
        payload = {
            'status': status,
            'command': command,
            'stdout': stdout
        }
        req = request.Request(url,
                              headers={'content-type': 'application/json'},
                              data=json.dumps(payload).encode('utf-8'))
        with request.urlopen(req) as response:
            code = response.getcode()
            charset = response.headers.get_content_charset('utf-8')
            body = json.loads(response.read().decode(charset))
            # print('{}, {}'.format(code, body))

    update_status('STARTED', None)
    time.sleep(5)
    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, encoding='utf-8')
    update_status('FINISHED', process.stdout)