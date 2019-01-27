from typing import Optional

import docker.errors
from docker import DockerClient
from docker.models.containers import Container

from .base import Operation


class RunRedis(Operation):
    def __init__(self, docker_client: DockerClient, container_name: str):
        super().__init__()
        self.docker = docker_client
        self.container_name = container_name

    def execute(self):
        """Run a redis container detached with `self.container_name` if there isn't one running already.

        :raise: docker.errors.ImageNotFound
        :raise: docker.errors.APIError
        """

        container = self._get_container(self.container_name)
        if container is not None:
            if container.status == 'running':
                return
            else:
                container.remove()

        self.docker.images.pull('redis', tag='latest')
        self.docker.containers.run('redis', detach=True, name=self.container_name)

    def _get_container(self, container_name: str) -> Optional[Container]:
        try:
            return self.docker.containers.get(container_name)
        except docker.errors.NotFound:
            return None
