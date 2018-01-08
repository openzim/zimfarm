import os, ftplib
from time import sleep
from datetime import datetime
from pathlib import Path

import docker
from docker import DockerClient

from .Base import ZimfarmTask
from utils.status import Status


class MWOffliner(ZimfarmTask):
    name = 'mwoffliner'

    def __init__(self):
        super().__init__()
        self.token: str = None
        self.total_steps = 4

        self.redis_name = os.getenv('REDIS_NAME', 'zimfarm_redis')
        self.host_working_dir = os.getenv('HOST_WORKING_DIR')
        self.container_working_dir = os.getenv('CONTAINER_WORKING_DIR')

    def run(self, config: {}):
        self.get_token()
        client = docker.from_env()

        self.start_time = datetime.utcnow()
        self.status = Status.PREPARING
        self.put_status()

        self.run_redis(client)
        self.pull_mwoffliner(client)

        self.status = Status.GENERATING
        self.put_status()
        self.generate(client, config)

        self.status = Status.UPLOADING
        self.put_status()
        self.upload_file()
        self.status = Status.FINISHED
        self.ended_time = datetime.utcnow()
        self.put_status()

    def run_redis(self, client: DockerClient):
        """
        Step 1 of 4: start redis container

        First, see if there is already a redis container with the same name.
        If there is and it is running, finish step successfully.
        If there is and it is nor running, remove it.
        Run a new redis container with the designated name.

        :param client: a docker connection
        """
        self.step_started(current=0, name='Start Redis')
        containers = client.containers.list(all=True, filters={'name': self.redis_name})

        if len(containers) > 0:
            for container in containers:
                if container.status == 'running':
                    self.step_finished(current=0, success=True)
                    return
                else:
                    container.remove()

        client.images.pull('redis', tag='latest')
        client.containers.run('redis', detach=True, name=self.redis_name)
        self.step_finished(current=0, success=True)

    def pull_mwoffliner(self, client: DockerClient):
        """
        Step 2 of 4: pull mwoffliner image

        :param client: a docker connection
        """

        self.step_started(current=1, name='Pull MWOffliner')
        client.images.pull('openzim/mwoffliner', tag='latest')
        self.step_finished(current=1, success=True)

    def generate(self, client: DockerClient, config: {}):
        """
        Step 3 of 4: run offliner and generate the zim file
        :param client:
        :param config:
        :return:
        """

        # command to be executed in the container
        def get_command(params: {}):
            params['redis'] = 'redis://redis'
            params['outputDirectory'] = '/output'
            parts: [str] = []
            for key, value in params.items():
                if isinstance(value, bool):
                    parts.append('--{name}'.format(name=key))
                else:
                    parts.append('--{name}={value}'.format(name=key, value=value))
            return 'mwoffliner {}'.format(' '.join(parts))

        # mwoffliner docker run options
        def get_options():
            working_dir = '{}/{}'.format(self.host_working_dir, self.request.id)
            options = {
                'name': '_'.join([MWOffliner.name, self.request.id]),
                'remove': True,
                'links': {self.redis_name: 'redis'},
                'stdout': True,
                'stderr': True,
                'volumes': {working_dir: {'bind': '/output', 'mode': 'rw'}},
            }

            cpu_quota = os.getenv('CPU_QUOTA')
            if cpu_quota is not None:
                cpu_quota = float(cpu_quota)
                if 0.0 < cpu_quota < 1.0:
                    options['cpu_quota'] = int(cpu_quota * 1000000)

            mem_limit = os.getenv('MEM_LIMIT')
            if mem_limit is not None:
                options['mem_limit'] = mem_limit

            return options

        name = 'Generate Zim File'
        self.step_started(current=2, name=name)
        command = get_command(config)
        if os.getenv('SHOW_COMMAND', False):
            self.logger.info('Exec: {}'.format(command))

        # TODO: - Also, we need to define what to do to recover the task
        start_time = datetime.utcnow()
        result = client.containers.run('openzim/mwoffliner', command, **get_options())
        elapsed_seconds = (datetime.utcnow() - start_time).seconds
        self.step_finished(current=2, success=True, stdout=result, elapsed_seconds=elapsed_seconds)

    def upload_file(self):
        """
        Step 4 of 4: upload zim file(s)

        :return:
        :raises ConnectionRefusedError: if cannot connect to warehouse after certain amount of retries
        """

        self.step_started(current=3, name='Upload Zim File')

        username = os.getenv('USERNAME')
        warehouse_host = os.getenv('WAREHOUSE_HOST')

        start_time = datetime.utcnow()

        retries = 3
        while retries > 0:
            try:
                with ftplib.FTP(warehouse_host, username, self.token) as ftp:
                    output = Path('{}/{}'.format(self.container_working_dir, self.request.id))
                    for child in output.iterdir():
                        if child.is_file():
                            file_name = child.parts[-1]
                            with open(child, 'rb') as file:
                                ftp.storbinary('STOR {}'.format(file_name), file)
                break
            except ConnectionRefusedError:
                sleep(5)
                retries -= 1
        else:
            raise ConnectionRefusedError()

        elapsed_seconds = (datetime.utcnow() - start_time).seconds
        self.step_finished(current=3, success=True, elapsed_seconds=elapsed_seconds)
