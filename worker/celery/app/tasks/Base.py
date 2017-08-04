import json
import os
import urllib.request
from datetime import datetime
from urllib.error import HTTPError

from celery import Task
from celery.utils.log import get_task_logger
from docker.errors import APIError, ContainerError, ImageNotFound

from encoder import JSONEncoder


class ZimfarmTask(Task):
    """abstract class for all zimfarm tasks"""

    abstract = True

    def __init__(self):
        super().__init__()
        self.token: str = None
        self.project_name = os.getenv('COMPOSE_PROJECT_NAME', 'zimfarm')
        self.logger = get_task_logger(__name__)
        self.start_time: datetime = None
        self.ended_time: datetime = None
        self.zim_file_name = None
        self.status = 'PENDING'
        self.current_index = 0
        self.steps = []

    def run(self, *args, **kwargs):
        pass

    def on_failure(self, error, task_id, args, kwargs, einfo):
        if isinstance(error, APIError):
            self.logger.error('DOCKER Error -- APIError: {}'.format(error))
            self.step_finished(False, {'description': error.explanation})
        elif isinstance(error, ContainerError):
            self.logger.error('DOCKER Error -- ContainerError: {}'.format(error))
            self.step_finished(False, {'stderr': error.stderr})
        elif isinstance(error, ImageNotFound):
            self.logger.error('DOCKER Error -- ImageNotFound: {}'.format(error))
            self.step_finished(False, {'description': error.explanation})
        else:
            self.logger.error('Unknown Error: {}'.format(error))
            self.step_finished(False, {'description': 'Unknown Error'})
        self.put_status()

    def step_started(self):
        index = self.current_index
        self.logger.info('Step {step}/{total} -- {description}'.format(
            step=index + 1, total=len(self.steps), description=self.steps[index]['name']))

    def step_finished(self, success: bool, meta: {}=None):
        index = self.current_index
        self.steps[index]['success'] = success
        if success == False:
            self.status = 'ERROR'
        if meta is not None:
            self.steps[index]['meta'] = meta

    def put_status(self):
        host = os.getenv('HOST')
        url = "https://{host}/api/task/{id}".format(host=host, id=self.request.id)
        payload = {
            'status': self.status,
            'steps': self.steps,
            'file_name': self.zim_file_name,
            'time_stamp': {
                'started': self.start_time,
                'ended': self.ended_time
            }
        }
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'token': self.token
        }
        request = urllib.request.Request(url, json.dumps(payload, cls=JSONEncoder).encode('utf-8'),
                                         headers, method='PUT')
        try:
            with urllib.request.urlopen(request) as response:
                code = response.code
        except HTTPError as error:
            code = error.code
