from enum import Enum
import json, subprocess, urllib.request
from celery import Celery


app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672')
# url_root = 'http://proxy/api/task/'
url_root = 'http://dispatcher_backend/task/'


class ZimfarmGenericTaskStatus(Enum):
    PENDING = 0
    UPDATING_CONTAINER = 1
    EXECUTING_SCRIPT = 2
    UPLOADING_FILES = 3
    FINISHED = 4
    ERROR = 100


@app.task(bind=True, name='zimfarm_generic')
def zimfarm_generic(self, image_name: str, script: str):
    def update_container(name: str):
        pass

    def update_status(status: ZimfarmGenericTaskStatus, stdout=None, stderr=None, return_code=None):
        url = url_root + self.request.id
        task = {'status': status.name}
        if stdout is not None: task['stdout'] = stdout
        if stderr is not None: task['stderr'] = stderr
        if return_code is not None: task['return_code'] = return_code
        payload = {'token': '', 'task': task}

        req = urllib.request.Request(url, headers={'content-type': 'application/json'},
                                     data=json.dumps(payload).encode('utf-8'))
        with urllib.request.urlopen(req) as response:
            pass

    def execute_script_sync(script: str):
        process = subprocess.run(["ls", "-l"], check=True, encoding='utf-8',
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout, process.stderr, process.returncode

    def upload_files():
        pass

    update_status(ZimfarmGenericTaskStatus.UPDATING_CONTAINER)
    update_container(image_name)
    update_status(ZimfarmGenericTaskStatus.EXECUTING_SCRIPT)
    stdout, stderr, return_code = execute_script_sync(script)
    update_status(ZimfarmGenericTaskStatus.UPLOADING_FILES, stdout, stderr, return_code)
    upload_files()
    update_status(ZimfarmGenericTaskStatus.FINISHED, stdout, stderr, return_code)
