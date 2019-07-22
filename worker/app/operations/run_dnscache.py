from typing import Optional

from docker import DockerClient
from docker.models.containers import Container

from .base import Operation
from utils.docker import remove_existing_container


class RunDNSCache(Operation):
    def __init__(self, docker_client: DockerClient, task_id: str):
        super().__init__()
        self.docker = docker_client
        self._container_name = f'dnscache_{task_id}'
        self._container: Optional[Container] = None

    def execute(self) -> Container:
        """Run a dnscache container detached.

        :raise: docker.errors.ImageNotFound
        :raise: docker.errors.APIError
        """

        if self._container:
            return self._container

        remove_existing_container(self.docker, name=self._container_name)

        image = self.docker.images.pull('openzim/dnscache', tag='latest')
        self._container = self.docker.containers.run(image, detach=True, name=self._container_name)
        return self._container

    def stop(self):
        remove_existing_container(self.docker, name=self._container_name)

    def __enter__(self):
        return self.execute()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
