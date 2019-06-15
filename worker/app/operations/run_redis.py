import os
from pathlib import Path
from typing import Optional

from docker import DockerClient
from docker.models.containers import Container

from .base import Operation
from utils.docker import remove_existing_container
from utils.settings import Settings


class RunRedis(Operation):
    def __init__(self, docker_client: DockerClient, task_id: str, working_dir_host: str):
        super().__init__()
        self.docker = docker_client
        self._container_name = f'redis_{task_id}'
        self._container: Optional[Container] = None
        self.redis_socket_name = f'redis_{task_id}.sock'
        self.sockets_dir_host = Path(working_dir_host).joinpath('sockets').absolute()

    def execute(self) -> Container:
        """Run a redis container detached.

        :raise: docker.errors.ImageNotFound
        :raise: docker.errors.APIError
        """

        if self._container:
            return self._container

        remove_existing_container(self.docker, name=self._container_name)

        image = self.docker.images.pull('redis', tag='latest')
        volumes = {self.sockets_dir_host: {'bind': Settings.sockets_dir_container,
                                           'mode': 'rw'}}
        self._container = self.docker.containers.run(
            image, command=self._get_command(), detach=True, name=self._container_name, volumes=volumes)
        return self._container

    def __enter__(self):
        return self.execute()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._container:
            self._container.stop()
            self._container.remove()

    def _get_command(self):
        redis_socket = os.path.join(Settings.sockets_dir_container, self.redis_socket_name)
        return f'redis-server --save "" --appendonly no --unixsocket {redis_socket} --unixsocketperm 744'
