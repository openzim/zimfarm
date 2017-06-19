from enum import Enum
import json, subprocess, urllib
from celery import Celery


app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672')
# url_root = 'http://proxy/api/task/'
url_root = 'http://dispatcher_backend/task/'


class ZimfarmGenericTaskStstus(Enum):
    PENDING = 'PENDING'
    UPDATING_CONTAINER = 'UPDATING_CONTAINER'
    EXECUTING_SCRIPT = 'EXECUTING_SCRIPT'
    UPLOADING_FILES = 'UPLOADING_FILES'
    FINISHED = 'FINISHED'
    ERROR = 'ERROR'


@app.task(bind=True, name='zimfarm_generic')
def zimfarm_generic(self, container_name: str, script: str):
    def update_container(name: str):
        pass

    def update_status(status: ZimfarmGenericTaskStstus):
        url = url_root + self.request.id
        payload = {'status': status.name}
        req = urllib.request.Request(url, headers={'content-type': 'application/json'},
                                     data=json.dumps(payload).encode('utf-8'))
        with urllib.request.urlopen(req) as response:
            pass

    def execute_script(script: str):
        pass

    def upload_files():
        pass

    update_status(ZimfarmGenericTaskStstus.UPDATING_CONTAINER)
    update_container(container_name)
    update_status(ZimfarmGenericTaskStstus.EXECUTING_SCRIPT)
    execute_script(script)
    update_status(ZimfarmGenericTaskStstus.UPLOADING_FILES)
    upload_files()
    update_status(ZimfarmGenericTaskStstus.FINISHED)



    # update_status('STARTED')
    # process = subprocess.run(script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # return_code = process.returncode
    # stdout = decode_bin_stream(process.stdout)
    # stderr = decode_bin_stream(process.stderr)
    # update_status('FINISHED', return_code, stdout, stderr)
