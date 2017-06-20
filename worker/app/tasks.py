from enum import Enum
import subprocess, shlex, json, urllib.request
from celery import Celery


app = Celery('worker', broker='amqp://admin:mypass@rabbit:5672')
# url_root = 'http://proxy/api/task/'
url_root = 'http://dispatcher_backend/task/'


class ZimfarmGenericTaskStatus(Enum):
    PENDING = 0
    UPDATING_CONTAINER = 1
    EXECUTING_SCRIPT = 2
    UPLOADING_FILES = 3
    CLEANING_UP = 4
    FINISHED = 5
    ERROR = 100


@app.task(bind=True, name='zimfarm_generic')
def zimfarm_generic(self, image_name: str, script: str):
    def update_container(name: str) -> (str, str, int):
        process = subprocess.run(["docker", "pull", name], encoding='utf-8', check=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout, process.stderr, process.returncode

    def execute_script_sync(task_id: str, image_name: str, script: str) -> (str, str, int):
        command = "docker run --name {container_name} {image_name} /bin/bash -c {script}"\
            .format(container_name=task_id, image_name=image_name, script=shlex.quote(script))
        process = subprocess.run(command, encoding='utf-8', check=True, shell=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout, process.stderr, process.returncode

    def clean_up(task_id: str):
        container_id = subprocess.run(["docker", "ps", "--filter", "name={}".format(task_id), "-a", "-q"],
                                      encoding='utf-8', stdout=subprocess.PIPE).stdout.rstrip()
        subprocess.run(["docker", "stop", container_id])
        subprocess.run(["docker", "rm", container_id])

    def update_status(status: ZimfarmGenericTaskStatus, stdout=None, stderr=None, return_code=None):
        url = url_root + self.request.id
        task = {'status': status.name}
        if stdout is not None: task['stdout'] = stdout
        if stderr is not None: task['stderr'] = stderr
        if return_code is not None: task['return_code'] = return_code
        payload = {'token': '', 'task': task}

        req = urllib.request.Request(url, headers={'content-type': 'application/json'},
                                     data=json.dumps(payload).encode('utf-8'))
        urllib.request.urlopen(req)

    def upload_files():
        pass

    def update_stream(new_result):
        nonlocal stdout, stderr, return_code
        stdout += new_result[0]
        stderr += new_result[1]
        return_code = new_result[2]

    stdout, stderr, return_code = '', '', 0

    try:
        update_status(ZimfarmGenericTaskStatus.UPDATING_CONTAINER)
        result = update_container(image_name)
        update_stream(result)

        update_status(ZimfarmGenericTaskStatus.EXECUTING_SCRIPT)
        result = execute_script_sync(self.request.id, image_name, script)
        update_stream(result)

        update_status(ZimfarmGenericTaskStatus.UPLOADING_FILES, stdout, stderr, return_code)
        upload_files()

        update_status(ZimfarmGenericTaskStatus.CLEANING_UP, stdout, stderr, return_code)
        clean_up(self.request.id)

        update_status(ZimfarmGenericTaskStatus.FINISHED, stdout, stderr, return_code)
    except subprocess.CalledProcessError as error:
        update_stream((error.stdout, error.stderr, error.returncode))

        update_status(ZimfarmGenericTaskStatus.CLEANING_UP, stdout, stderr, return_code)
        clean_up(self.request.id)

        update_status(ZimfarmGenericTaskStatus.ERROR, stdout, stderr, error.returncode)
