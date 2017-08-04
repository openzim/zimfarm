import os
from datetime import datetime
from pathlib import Path

import docker
from docker import DockerClient

from .Base import ZimfarmTask


class MWOffliner(ZimfarmTask):
    name = 'mwoffliner'

    def __init__(self):
        super().__init__()
        self.steps = [
            {'name': 'Start Redis'},
            {'name': 'Pull MWOffliner'},
            {'name': 'Generate Zim'},
            {'name': 'Upload Zim'},
        ]
        self.host_redis_name = '_'.join([self.project_name, 'redis'])
        self.offliner_output_path = os.getenv('OFFLINER_OUTPUT_PATH', '/')
        self.worker_running_output_path = Path("/ZimFileOutput/running")
        self.worker_finished_output_path = Path("/ZimFileOutput/finished")

    def run(self, token: str, config: {}):
        self.token = token
        client = docker.from_env()

        self.start_time = datetime.utcnow()
        self.status = 'PREPARING'
        self.put_status()

        self.run_redis(client)
        self.pull_mwoffliner(client)

        self.status = 'GENERATING'
        self.put_status()
        self.generate(client, config)

        # self.status = 'UPLOADING'
        # self.put_status()
        # self.upload_file()
        self.status = 'FINISHED'
        self.ended_time = datetime.utcnow()
        self.put_status()

    def run_redis(self, client: DockerClient):
        self.current_index = 0
        self.step_started()

        containers = client.containers.list(filters={'name': self.host_redis_name})
        if len(containers) == 0:
            client.images.pull('redis', tag='latest')
            client.containers.run('redis', detach=True, name=self.host_redis_name)
        self.step_finished(True)

    def pull_mwoffliner(self, client: DockerClient):
        self.current_index = 1
        self.step_started()
        client.images.pull('openzim/mwoffliner', tag='latest')
        self.step_finished(True)

    def generate(self, client: DockerClient, config: {}):
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
            options = {
                'name': '_'.join([self.project_name, self.request.id]),
                'remove': True,
                'links': {self.host_redis_name: 'redis'},
                'stdout': True,
                'stderr': True,
                'volumes': {self.offliner_output_path: {'bind': '/output', 'mode': 'rw'}},
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

        self.current_index = 2
        self.step_started()

        command = get_command(config)
        if os.getenv('SHOW_COMMAND', False):
            self.logger.info('Exec: {}'.format(command))

        start_time = datetime.utcnow()

        # TODO: - when container returns none zero exit code, aka when docker.errors.ContainerError is raized result is a `bytes` object and it is not json serializeable. Also, we need to define what to do to recover the task
        result = client.containers.run('openzim/mwoffliner', command, **get_options()).decode('utf-8')
        elapsed_seconds = (datetime.utcnow() - start_time).seconds
        self.step_finished(True, {
            'stdout': result,
            'elapsed_seconds': elapsed_seconds
        })

        # get output zim file name
        # for content in self.worker_running_output_path.joinpath(self.request.id).iterdir():
        #     if not content.is_dir():
        #         self.zim_file_name = str(content.parts[-1])

    def upload_file(self):
        self.current_index = 3
        self.step_started()

        start_time = datetime.utcnow()

        if not self.worker_finished_output_path.exists():
            os.makedirs(str(self.worker_finished_output_path))

        output = self.worker_running_output_path.joinpath(self.request.id)
        for source in output.iterdir():
            if not source.is_dir():
                destination = self.worker_finished_output_path.joinpath(source.parts[-1])
                os.rename(str(source), str(destination))
        os.removedirs(str(output))

        # remote_shell = 'ssh -p {port} -i {private_key} -oStrictHostKeyChecking=no' \
        #     .format(port=os.getenv('RSYNC_PORT', 22), private_key='/usr/src/id_rsa')
        # subprocess.run('rsync -azh -e="{remote_shell}" /mnt/ZimOutput/{id}/ root@{remote_host}:/zimfiles'
        #                .format(remote_shell=remote_shell, id=self.request.id, remote_host=os.getenv('RSYNC_HOST')),
        #                shell=True)

        elapsed_seconds = (datetime.utcnow() - start_time).seconds
        self.step_finished(True, {
            'elapsed_seconds': elapsed_seconds
        })
