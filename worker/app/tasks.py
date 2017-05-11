import time
import subprocess
from urllib import request, response, parse
import json
from celery import Celery, Task


app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672', backend='redis://redis:6379/0')


@app.task(bind=True, name='subprocess')
def subprocess_run(self, command: str):
    def update_status(status:str, stdout: str, stderr: str):
        url = 'http://proxy/api/task/' + self.request.id
        payload = {
            'status': status,
            'command': command,
            'stdout': stdout, 
            'stderr': stderr
        }
        req = request.Request(url,
                              headers={'content-type': 'application/json'},
                              data=json.dumps(payload).encode('utf-8'))
        with request.urlopen(req) as response:
            code = response.getcode()
            charset = response.headers.get_content_charset('utf-8')
            body = json.loads(response.read().decode(charset))
            # print('{}, {}'.format(code, body))
            # TODO: retry if a POST failed (code != 200)
    
    def decode_bin_stream(bin) -> str:
        return bin.decode('utf-8') if bin is not None else None

    update_status('STARTED', None, None)
    time.sleep(5)

    process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = decode_bin_stream(process.stdout)
    stderr = decode_bin_stream(process.stderr)
    
    update_status('UPLOADING', stdout, stderr)
    time.sleep(5)

    if stderr == '':
        update_status('FINISHED', stdout, stderr)
    else:
        update_status('ERROR', stdout, stderr)