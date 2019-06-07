from typing import Optional

from docker import DockerClient
from docker.models.containers import Container

from .base import Operation
from utils.settings import Settings


class RunSocket(Operation):
    def __init__(self, docker_client: DockerClient, task_id: str):
        super().__init__()
        self.docker = docker_client
        self._container_name = f'socket_{task_id}'
        self._container: Optional[Container] = None

    def execute(self) -> Container:
        """Run a busybox container detached.

        :raise: docker.errors.ImageNotFound
        :raise: docker.errors.APIError
        """

        if self._container:
            return self._container

        self._remove_existing()

        image = self.docker.images.pull('busybox', tag='latest')
        volumes = {Settings.sockets_dir_host: {'bind': Settings.sockets_dir_container,
                                               'mode': 'rw'}}
        self._container = self.docker.containers.run(
            image, detach=True,
            command=f'chmod -R 777 {Settings.sockets_dir_container}',
            volumes=volumes, name=self._container_name)
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
