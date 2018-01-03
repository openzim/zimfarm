import json
import os
import urllib.request
from datetime import datetime, timedelta
from urllib.error import HTTPError

from celery import Task
from celery.utils.log import get_task_logger
import docker.errors as DockerError

from utils.encoder import JSONEncoder
from utils.status import Status


class ZimfarmTask(Task):
    """abstract class for all zimfarm tasks"""

    abstract = True

    def __init__(self):
        super().__init__()
        self.logger = get_task_logger(__name__)

        self.status: Status = Status['PENDING']
        self.total_steps = 0
        self.steps = []
        self.start_time: datetime = None
        self.ended_time: datetime = None

    def on_failure(self, error, task_id, args, kwargs, einfo):
        current_step = len(self.steps) - 1
        if isinstance(error, DockerError.APIError):
            self.logger.error('DOCKER Error -- APIError: {}'.format(error))
            self.step_finished(current_step, False, **{'description': error.explanation})
        elif isinstance(error, DockerError.ContainerError):
            self.logger.error('DOCKER Error -- ContainerError: {}'.format(error))
            self.step_finished(current_step, False, **{'stderr': error.stderr})
        elif isinstance(error, DockerError.ImageNotFound):
            self.logger.error('DOCKER Error -- ImageNotFound: {}'.format(error))
            self.step_finished(current_step, False, **{'description': error.explanation})
        elif isinstance(error, ConnectionRefusedError):
            self.logger.error('Uploading Error -- Connection Refused')
            self.step_finished(current_step, False, **{'description': 'Uploading Error -- Connection Refused'})
        else:
            self.logger.error('Unknown Error: {}'.format(error))
            self.step_finished(current_step, False, **{'description': 'Unknown Error'})
        self.put_status()

    def step_started(self, current: int, name: str):
        self.logger.info('Step {current}/{total} -- {name}'.format(current=current + 1, total=self.total_steps, name=name))
        if current >= len(self.steps):
            self.steps.append({'name': name})

    def step_finished(self, current: int, success: bool, **kwargs):
        self.steps[current]['success'] = success
        if not success:
            self.status = Status['ERROR']
        if kwargs is not None:
            for key, value in kwargs.items():
                self.steps[current][key] = value

    def put_status(self):
        host = os.getenv('DISPATCHER_HOST')
        url = "https://{host}/api/task/{id}".format(host=host, id=self.request.id)
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'token': self.token
        }
        payload = {'status': self.status}
        if self.start_time is not None and self.ended_time is not None:
            delta = self.ended_time - self.start_time
            if delta >= timedelta(seconds=0):
                payload['elapsed_second'] = delta.seconds
        request = urllib.request.Request(url, json.dumps(payload, cls=JSONEncoder).encode('utf-8'),
                                         headers, method='PUT')
        try:
            with urllib.request.urlopen(request) as response:
                code = response.code
        except HTTPError as error:
            code = error.code