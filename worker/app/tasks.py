import subprocess
from celery import Task
from celery.utils.log import get_task_logger
import docker


logger = get_task_logger(__name__)


class Generic(Task):
    name = 'zimfarm.generic'
    def run(self, image_name: str, script: str):
        client = docker.from_env()
        print(client.containers.run("alpine", ["echo", "hello", "world"]))
        # try:
        #     stdout, stderr, returncode = docker.pull(image_name)
        #     logger.info('task finished, {}, {}, {}'.format(stdout, stderr, returncode))
        # except subprocess.CalledProcessError as e:
        #     logger.info('task failed, {}, {}, {}, {}'.format(e.cmd, e.stdout, e.stderr, e.returncode))


class MWOffliner(Task):
    name = 'zimfarm.mwoffliner'
    def run(self):
        docker.from_env()
        # docker.pull('mwoffliner')
        pass