import os
import asyncio
from pathlib import Path

from docker import DockerClient
from docker.models.containers import Container

from .base import Operation, ContainerResult
from utils.settings import Settings
from .upload import Upload


class RunMWOffliner(Operation):
    """Run MWOffliner container with `config`"""

    def __init__(self, docker_client: DockerClient, tag: str, flags: {}, task_id: str, working_dir_host: str,
                 redis_container: Container, dns: str):
        tag = 'latest' if not tag else tag
        super().__init__()
        self.docker = docker_client
        self.working_dir_host = Path(working_dir_host).joinpath(task_id).absolute()
        self.sockets_dir_host = Path(working_dir_host).joinpath('sockets').absolute()
        self.redis_container = redis_container
        self.image_name = 'openzim/mwoffliner:{}'.format(tag)
        self.image_tag = tag
        self.dns = dns
        self.container_name = f'mwoffliner_{task_id}'
        self.redis_socket_name = f'redis_{task_id}.sock'
        self.command = self._get_command(flags)

    def execute(self) -> ContainerResult:
        """Pull and run mwoffliner"""

        # pull mwoffliner image
        self.docker.images.pull(self.image_name)

        # run mwoffliner
        volumes = {self.working_dir_host: {'bind': '/output', 'mode': 'rw'},
                   self.sockets_dir_host: {'bind': Settings.sockets_dir_container,
                                           'mode': 'rw'}}
        container: Container = self.docker.containers.run(
            image=self.image_name, command=self.command, volumes=volumes, detach=True,
            name=self.container_name, dns=self.dns)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._wait_for_finish(container.id))

        container.reload()

        container_log = Upload.upload_log(container)

        exit_code = container.attrs['State']['ExitCode']
        stdout = container.logs(stdout=True, stderr=False, tail=100).decode("utf-8")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8")
        result = ContainerResult(self.image_name, self.command, exit_code, stdout, stderr, container_log)

        container.remove()

        return result

    def _get_command(self, flags: {}):
        flags['redis'] = os.path.join(Settings.sockets_dir_container, self.redis_socket_name)
        flags['outputDirectory'] = '/output'
        params: [str] = []
        for key, value in flags.items():
            if value is True:
                params.append('--{name}'.format(name=key))
            elif isinstance(value, list):
                for item in value:
                    params.append('--{name}="{value}"'.format(name=key, value=item))
            else:
                params.append('--{name}="{value}"'.format(name=key, value=value))
        return 'mwoffliner {}'.format(' '.join(params))
