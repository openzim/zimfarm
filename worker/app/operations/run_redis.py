import os
from typing import Optional

from docker import DockerClient
from docker.models.containers import Container

from .base import Operation
from utils.settings import Settings


class RunRedis(Operation):
    def __init__(self, docker_client: DockerClient, task_id: str):
        super().__init__()
        self.docker = docker_client
        self.task_id = task_id
        self._container_name = f'redis_{task_id}'
        self._socket_container_name = f'socket_{task_id}'
        self._container: Optional[Container] = None

    def execute(self) -> Container:
        """Run a redis container detached.

        :raise: docker.errors.ImageNotFound
        :raise: docker.errors.APIError
        """

        if self._container:
            return self._container

        self._remove_existing()

        image = self.docker.images.pull('redis', tag='latest')
        self._container = self.docker.containers.run(
            image, command=self._get_command(), detach=True,
            name=self._container_name, volumes_from=self._socket_container_name)
        return self._container

    def __enter__(self):
        return self.execute()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._container:
            self._container.stop()
            self._container.remove()

    def _remove_existing(self):
        containers = self.docker.containers.list(all=True, filters={'name': self._container_name})
        if containers:
            container = containers[0]
            container.stop()
            container.remove()

    def _get_command(self):
        redis_socket = os.path.join(Settings.sockets_dir_container,
                                    f'redis_{self.task_id}.sock')
        return f'redis-server --save "" --appendonly no --unixsocket {redis_socket} --unixsocketperm 744'
