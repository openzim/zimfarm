import os
from typing import Optional

import docker
from docker import DockerClient
from docker.models.containers import Container

from .base import Operation
from utils.docker import get_ip_address, remove_existing_container


class RunDNSCache(Operation):
    def __init__(self, docker_client: DockerClient, task_id: str):
        super().__init__()
        self.docker = docker_client
        self.container_name = f'dnscache_{task_id}'
        self._container: Optional[Container] = None

    def execute(self) -> Container:
        """Run a dnscache container detached.

        :raise: docker.errors.ImageNotFound
        :raise: docker.errors.APIError
        """

        if self._container:
            return self._container

        remove_existing_container(self.docker, name=self.container_name)

        environment = {"USE_PUBLIC_DNS": os.getenv("USE_PUBLIC_DNS", "no")}
        image = self.docker.images.pull('openzim/dnscache', tag='latest')
        self._container = self.docker.containers.run(image, detach=True, name=self.container_name, environment=environment)
        return self._container

    def get_ip_addresses(self):
        return [get_ip_address(docker.from_env(), self.container_name)]

    @property
    def ip_address(self):
        addresses = self.get_ip_addresses()
        return addresses[-1] if len(addresses) else None

    def stop(self):
        remove_existing_container(self.docker, name=self.container_name)

    def __enter__(self):
        return self.execute()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
